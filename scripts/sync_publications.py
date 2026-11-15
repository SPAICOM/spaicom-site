#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
#     "requests",
# ]
# ///
"""
Create or update publication pages from the (optional) "publications" tab of the Google Sheet.
New papers are normally added with `just discover`; this tab is for extras.

A row needs `id` (a DOI or an arXiv ID); `pdf_url`, `code_url` and `type` are the other columns to fill. For every row whose
paper is not on the site yet, this script

  1. fetches the metadata (Crossref for DOIs, arXiv for arXiv IDs),
  2. matches the authors against the profiles in content/authors/,
  3. writes content/publication/<slug>/index.md and cite.bib.

It is deliberately conservative:

  * it never deletes pages, and it edits existing pages in place, touching only the
    fields listed under "Updates" below, so hand edits (featured image, body text,
    curated abstract and authors) are safe;
  * a paper that looks like a duplicate of an existing page (same title but a
    different DOI, e.g. a preprint that was later published) is reported, not
    written;
  * authors that cannot be matched to a profile are kept as plain names and
    listed in the report.

Sheet columns (header names are case-insensitive, extra columns are ignored):

  id           DOI (10.xxxx/...) or arXiv ID (2403.12345). Leave empty for manual rows.
  type         conference | journal | preprint. Auto-detected when empty.
  title, venue, venue_short, year, authors, abstract
               Only needed for rows without an id, or to override the fetched value.
               `authors` is "Given Family; Given Family; ...".
  pdf_url, code_url, dataset_url, slides_url, video_url, project_url, poster_url
  featured     yes/true/1 to show the paper in the Featured widget.
  tags         ";"-separated list.
  replaces     DOI, arXiv ID or page folder of an existing page that this row supersedes
               (e.g. the arXiv preprint of a paper that is now published).
  update       yes = re-fetch the metadata and refresh the existing page (title, date,
               venue, abstract, authors). Remove or clear it afterwards.

Updates (what happens to a paper that is already on the site):

  * Sheet-owned fields: link columns, `featured` and `tags` are copied to the page when
    the cell is non-empty and different. An empty cell never clears a value.
  * Preprint -> published: a new DOI whose title matches (or is very similar to) an
    existing preprint page, or a row with `replaces`, updates that page in place:
    title, doi, type, venue, date and cite.bib. Authors, abstract, links, tags, images
    and the body are kept.
  * `update = yes`: also replaces authors and the abstract with the fetched ones.

Configuration (environment variables, see .env.example):

  SPAICOM_SHEET_ID             Google Sheet ID
  SPAICOM_PUBLICATIONS_GID     GID of the publications tab (optional: no tab, nothing to do)
  CROSSREF_MAILTO              optional; puts requests in Crossref's "polite pool"
"""

import argparse
import csv
import difflib
import io
import json
import os
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import requests
import yaml

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.download_utils import download_sheet_as_csv

PUBLICATION_DIR = Path("content/publication")
AUTHORS_DIR = Path("content/authors")

TYPE_TO_CSL = {
    "conference": "paper-conference",
    "journal": "article-journal",
    "preprint": "article",
}
CROSSREF_TYPE = {
    "proceedings-article": "conference",
    "journal-article": "journal",
    "posted-content": "preprint",
}

ARXIV_RE = re.compile(
    r"(?:arxiv[:.\s/]*(?:abs/|pdf/)?)?(\d{4}\.\d{4,5})(?:v\d+)?", re.IGNORECASE
)
ARXIV_DOI_RE = re.compile(r"^10\.48550/arxiv\.(.+)$", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def ascii_norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", "", text.lower())).strip()


def slugify(text: str) -> str:
    return re.sub(r"\s+", "-", ascii_norm(text))[:120].strip("-")


def q(value: str) -> str:
    """Quote a string as a YAML double-quoted scalar (JSON strings are valid YAML)."""
    return json.dumps(" ".join((value or "").split()), ensure_ascii=False)


def normalize_doi(doi: str) -> str:
    """Strip URL/`doi:` prefixes. Case is kept; compare with `.lower()`."""
    doi = (doi or "").strip()
    return re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi, flags=re.IGNORECASE)


def truthy(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "y", "x"}


def split_list(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(";") if v.strip()]


_last_arxiv_call = 0.0


def http_get(
    url: str, *, headers: dict | None = None, retries: int = 4
) -> requests.Response:
    global _last_arxiv_call
    headers = {"User-Agent": "spaicom-site-sync", **(headers or {})}
    last: Exception | None = None
    for attempt in range(retries):
        if "arxiv.org" in url:  # arXiv asks for at most one request every 3 seconds
            wait = 3.0 - (time.monotonic() - _last_arxiv_call)
            if wait > 0:
                time.sleep(wait)
            _last_arxiv_call = time.monotonic()
        try:
            resp = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
            if resp.status_code in (429, 500, 502, 503, 504):
                retry_after = resp.headers.get("Retry-After", "")
                delay = int(retry_after) if retry_after.isdigit() else 5 * (attempt + 1)
                last = requests.HTTPError(f"HTTP {resp.status_code}")
                time.sleep(min(delay, 30))
                continue
            return resp
        except requests.RequestException as exc:  # network error
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Could not reach {url}: {last}")


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


@dataclass
class Paper:
    title: str = ""
    authors: list[str] = field(default_factory=list)  # "Given Family"
    date: str = ""  # YYYY-MM-DD
    venue: str = ""
    venue_short: str = ""
    abstract: str = ""
    type: str = ""  # conference | journal | preprint
    doi: str = ""
    arxiv: str = ""
    pdf_url: str = ""
    bibtex: str = ""


def _date_from_parts(parts: list | None) -> str:
    if not parts or not parts[0]:
        return ""
    y, m, d = (list(parts) + [1, 1])[:3]
    return f"{int(y):04d}-{int(m or 1):02d}-{int(d or 1):02d}"


def fetch_crossref(doi: str) -> Paper:
    params = os.environ.get("CROSSREF_MAILTO")
    url = f"https://api.crossref.org/works/{doi}" + (
        f"?mailto={params}" if params else ""
    )
    resp = http_get(url)
    if resp.status_code == 404:
        raise LookupError(f"DOI {doi} was not found in Crossref")
    resp.raise_for_status()
    msg = resp.json()["message"]

    authors = []
    for a in msg.get("author", []):
        name = " ".join(x for x in (a.get("given", ""), a.get("family", "")) if x)
        authors.append(name or a.get("name", ""))

    date = ""
    for key in ("published", "published-print", "published-online", "issued"):
        date = _date_from_parts((msg.get(key) or {}).get("date-parts", [[None]])[0])
        if date:
            break

    abstract = re.sub(r"<[^>]+>", " ", msg.get("abstract", "") or "")
    abstract = re.sub(
        r"^\s*Abstract\s*[:.]?\s*", "", " ".join(abstract.split()), flags=re.IGNORECASE
    )

    short = (msg.get("short-container-title") or [""])[0]
    venue = (msg.get("container-title") or [""])[0]
    ptype = CROSSREF_TYPE.get(msg.get("type", ""), "")
    if ptype == "conference" and not venue:
        venue = (msg.get("event") or {}).get("name", "")

    if not abstract:
        abstract = fetch_openalex_abstract(doi)

    return Paper(
        title=(msg.get("title") or [""])[0],
        authors=authors,
        date=date,
        venue=venue,
        venue_short=short,
        abstract=abstract,
        type=ptype,
        doi=doi,
        bibtex=fetch_doi_bibtex(doi),
    )


def fetch_openalex_abstract(doi: str) -> str:
    """Crossref often has no abstract; OpenAlex frequently does."""
    try:
        resp = http_get(
            f"https://api.openalex.org/works/doi:{doi}?select=abstract_inverted_index"
        )
        if resp.status_code != 200:
            return ""
        index = resp.json().get("abstract_inverted_index") or {}
    except (RuntimeError, ValueError):
        return ""
    words = {pos: word for word, positions in index.items() for pos in positions}
    return " ".join(words[i] for i in sorted(words))


def format_bibtex(text: str) -> str:
    """Re-emit one BibTeX entry with one field per line (doi.org returns a single line).

    Entries that are already multi-line, or that cannot be parsed, are returned unchanged.
    """
    text = text.strip()
    m = re.match(r"^@(\w+)\s*\{\s*([^,\s]*)\s*,(.*)\}\s*$", text, re.DOTALL)
    if not m or "\n" in text:
        return text + "\n" if text else text
    kind, key, body = m.groups()
    fields, depth, quoted, cur = [], 0, False, ""
    for ch in body:
        if ch == '"' and depth == 0:
            quoted = not quoted
        elif ch == "{" and not quoted:
            depth += 1
        elif ch == "}" and not quoted:
            depth -= 1
        if ch == "," and depth == 0 and not quoted:
            fields.append(cur.strip())
            cur = ""
        else:
            cur += ch
    if cur.strip():
        fields.append(cur.strip())
    if depth != 0 or quoted or not fields:
        return text + "\n"
    lines = ",\n".join(f"  {f}" for f in fields)
    return f"@{kind}{{{key},\n{lines}\n}}\n"


def fetch_doi_bibtex(doi: str) -> str:
    try:
        resp = http_get(
            f"https://doi.org/{doi}", headers={"Accept": "application/x-bibtex"}
        )
        if resp.status_code == 200 and resp.text.strip().startswith("@"):
            return format_bibtex(resp.text)
    except RuntimeError:
        pass
    return ""


def fetch_arxiv(arxiv_id: str) -> Paper:
    resp = http_get(f"https://export.arxiv.org/api/query?id_list={arxiv_id}")
    resp.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    entry = ET.fromstring(resp.content).find("a:entry", ns)
    if entry is None or entry.find("a:title", ns) is None:
        raise LookupError(f"arXiv ID {arxiv_id} was not found")
    title = " ".join(entry.findtext("a:title", "", ns).split())
    if title.lower() == "error":
        raise LookupError(f"arXiv ID {arxiv_id} was not found")
    authors = [
        " ".join(a.findtext("a:name", "", ns).split())
        for a in entry.findall("a:author", ns)
    ]
    published = entry.findtext("a:published", "", ns)[:10]
    paper = Paper(
        title=title,
        authors=authors,
        date=published,
        venue="arXiv preprint",
        abstract=" ".join(entry.findtext("a:summary", "", ns).split()),
        type="preprint",
        arxiv=arxiv_id,
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
    )
    paper.bibtex = build_bibtex(paper)
    return paper


def build_bibtex(p: Paper) -> str:
    first = ascii_norm(p.authors[0].split()[-1]) if p.authors else "anon"
    year = p.date[:4] or "nd"
    key = f"{first}{year}{ascii_norm(p.title.split()[0]) if p.title else ''}".replace(
        " ", ""
    )
    fields = {
        "title": p.title,
        "author": " and ".join(p.authors),
        "year": year,
        "journal" if p.type == "journal" else "howpublished": p.venue,
        "doi": p.doi,
        "eprint": p.arxiv,
        "archivePrefix": "arXiv" if p.arxiv else "",
    }
    body = ",\n".join(f"  {k}={{{v}}}" for k, v in fields.items() if v)
    kind = "article" if p.type == "journal" else "misc"
    return f"@{kind}{{{key},\n{body}\n}}\n"


def classify(identifier: str) -> tuple[str, str]:
    """Return (kind, normalized id) where kind is 'doi', 'arxiv' or 'manual'."""
    ident = identifier.strip()
    if not ident:
        return "manual", ""
    doi = normalize_doi(ident)
    m = ARXIV_DOI_RE.match(doi)
    if m:
        return "arxiv", re.sub(r"v\d+$", "", m.group(1))
    if doi.startswith("10."):
        return "doi", doi
    m = ARXIV_RE.search(ident)
    if m:
        return "arxiv", m.group(1)
    raise ValueError(
        f"'{identifier}' is neither a DOI (10.xxxx/...) nor an arXiv ID (2403.12345)"
    )


# ---------------------------------------------------------------------------
# Existing content
# ---------------------------------------------------------------------------


def read_front_matter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.DOTALL)
    if not m:
        return {}
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return {}


@dataclass
class Existing:
    slugs: set[str] = field(default_factory=set)
    dois: dict[str, str] = field(default_factory=dict)
    arxivs: dict[str, str] = field(default_factory=dict)
    titles: dict[str, str] = field(default_factory=dict)
    types: dict[str, str] = field(default_factory=dict)  # slug -> CSL type


def load_existing(pub_dir: Path) -> Existing:
    ex = Existing()
    for folder in sorted(pub_dir.glob("*/")):
        index = folder / "index.md"
        if not index.exists():
            continue
        slug = folder.name
        fm = read_front_matter(index)
        ex.slugs.add(slug)
        doi = normalize_doi(str(fm.get("doi") or "")).lower()
        if doi:
            ex.dois[doi] = slug
            m = ARXIV_DOI_RE.match(doi)
            if m:
                ex.arxivs[m.group(1)] = slug
        for url in (fm.get("url_pdf"), fm.get("url_source")):
            m = re.search(
                r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})",
                str(url or ""),
                re.IGNORECASE,
            )
            if m:
                ex.arxivs[m.group(1)] = slug
        if fm.get("title"):
            ex.titles[ascii_norm(str(fm["title"]))] = slug
        ex.types[slug] = str((fm.get("publication_types") or [""])[0])
    return ex


# ---------------------------------------------------------------------------
# Author matching
# ---------------------------------------------------------------------------


@dataclass
class Profile:
    slug: str
    first: str
    last: str


def load_profiles(authors_dir: Path) -> list[Profile]:
    profiles = []
    for index in sorted(authors_dir.glob("*/_index.md")):
        fm = read_front_matter(index)
        if fm.get("first_name") and fm.get("last_name"):
            profiles.append(
                Profile(index.parent.name, str(fm["first_name"]), str(fm["last_name"]))
            )
    return profiles


def match_author(name: str, profiles: list[Profile]) -> tuple[str | None, bool]:
    """Return (slug or None, ambiguous)."""
    full = ascii_norm(name)
    exact = [p for p in profiles if ascii_norm(f"{p.first} {p.last}") == full]
    if len(exact) == 1:
        return exact[0].slug, False

    candidates = []
    for p in profiles:
        last = ascii_norm(p.last)
        if not full.endswith(last) or (
            len(full) > len(last) and full[-len(last) - 1] != " "
        ):
            continue
        given = full[: len(full) - len(last)].split()
        first_tokens = ascii_norm(p.first).split()
        if not given or not first_tokens:
            continue
        g = given[0]
        if len(g) > 1 and g != first_tokens[0]:
            continue  # a spelled-out first name that differs
        if g[0] != first_tokens[0][0]:
            continue
        candidates.append(p)
    if len(candidates) == 1:
        return candidates[0].slug, False
    return None, len(candidates) > 1


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_index(p: Paper, authors: list[str], row: dict) -> str:
    iso = f"{p.date}T00:00:00Z"
    csl = TYPE_TO_CSL[p.type]
    if p.type == "conference":
        publication = f"In *{p.venue}*" if p.venue else ""
        short = f"In *{p.venue_short}*" if p.venue_short else ""
    else:
        publication = f"*{p.venue}*" if p.venue else ""
        short = f"*{p.venue_short}*" if p.venue_short else ""
    tags = split_list(row.get("tags", ""))
    pdf = row.get("pdf_url") or p.pdf_url

    lines = [
        "---",
        f"title: {q(p.title)}",
        "authors:",
        *[f"  - {q(a)}" for a in authors],
        f"date: '{iso}'",
        f"doi: {q(p.doi)}",
        f"publishDate: '{iso}'",
        f"publication_types: ['{csl}']",
        f"publication: {q(publication)}",
        f"publication_short: {q(short)}",
        f"abstract: {q(p.abstract)}",
        "summary: ''",
        "tags:" if tags else "tags: []",
        *[f"  - {q(t)}" for t in tags],
        f"featured: {'true' if truthy(row.get('featured', '')) else 'false'}",
        f"url_pdf: {q(pdf)}",
        f"url_code: {q(row.get('code_url', ''))}",
        f"url_dataset: {q(row.get('dataset_url', ''))}",
        f"url_poster: {q(row.get('poster_url', ''))}",
        f"url_project: {q(row.get('project_url', ''))}",
        f"url_slides: {q(row.get('slides_url', ''))}",
        "url_source: ''",
        f"url_video: {q(row.get('video_url', ''))}",
        "projects: []",
        "slides: ''",
        "---",
        "",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# In-place updates of existing pages
# ---------------------------------------------------------------------------

# Sheet column -> front matter key. When the cell is non-empty it is the master value.
SHEET_FIELDS = {
    "pdf_url": "url_pdf",
    "code_url": "url_code",
    "dataset_url": "url_dataset",
    "poster_url": "url_poster",
    "project_url": "url_project",
    "slides_url": "url_slides",
    "video_url": "url_video",
}


def render_key(key: str, value) -> list[str]:
    """Front matter lines for one top-level key, in the style of generated pages."""
    if key == "date":
        return [f"date: '{value}T00:00:00Z'"]
    if key == "publication_types":
        return [f"publication_types: ['{value}']"]
    if isinstance(value, bool):
        return [f"{key}: {'true' if value else 'false'}"]
    if isinstance(value, list):
        if not value:
            return [f"{key}: []"]
        return [f"{key}:", *[f"  - {q(str(v))}" for v in value]]
    return [f"{key}: {q(str(value))}"]


def set_keys(text: str, updates: dict) -> str:
    """Replace (or append) top-level front matter keys, leaving everything else untouched.

    Comments, key order, the page body and any hand-added fields are preserved.
    """
    m = re.match(r"^(---[ \t]*\n)(.*?)(\n---[ \t]*(?:\n|$))(.*)$", text, re.DOTALL)
    if not m:
        raise ValueError("no front matter")
    head, body, sep, rest = m.groups()
    lines = body.split("\n")
    for key, value in updates.items():
        new = render_key(key, value)
        start = next(
            (i for i, ln in enumerate(lines) if ln.startswith(f"{key}:")), None
        )
        if start is None:
            lines.extend(new)
            continue
        end = start + 1
        while end < len(lines) and lines[end] and lines[end][0] in " \t-":
            end += 1  # indented lines / list items belong to the key
        lines[start:end] = new
    return head + "\n".join(lines) + sep + rest


def _same(key: str, old, new) -> bool:
    if key == "date":
        return str(old or "")[:10] == str(new)[:10]
    if key == "doi":
        return normalize_doi(str(old or "")).lower() == normalize_doi(str(new)).lower()
    if key == "title":
        return ascii_norm(str(old or "")) == ascii_norm(str(new))
    if key == "publication_types":
        return (old or [""])[0] == new
    if key == "authors":
        return [str(a) for a in old or []] == [str(a) for a in new]
    if isinstance(new, bool):
        return bool(old) == new
    if isinstance(new, list):
        return [str(t) for t in old or []] == new
    return str(old or "").strip() == str(new).strip()


def sheet_updates(row: dict, fm: dict) -> dict:
    """Fields the sheet owns. Empty cells never clear a value on the page."""
    wanted: dict = {}
    for col, key in SHEET_FIELDS.items():
        if (row.get(col) or "").strip():
            wanted[key] = row[col].strip()
    if (row.get("featured") or "").strip():
        wanted["featured"] = truthy(row["featured"])
    if (row.get("tags") or "").strip():
        wanted["tags"] = split_list(row["tags"])
    return {k: v for k, v in wanted.items() if not _same(k, fm.get(k), v)}


def metadata_updates(
    paper: "Paper", fm: dict, author_values: list[str], refresh: bool
) -> dict:
    """Changes from freshly fetched metadata.

    `refresh` (explicit `update` column) also replaces authors and the abstract; a
    preprint -> published upgrade keeps the curated authors and abstract.
    """
    if paper.type == "conference":
        publication = f"In *{paper.venue}*" if paper.venue else ""
        short = f"In *{paper.venue_short}*" if paper.venue_short else ""
    else:
        publication = f"*{paper.venue}*" if paper.venue else ""
        short = f"*{paper.venue_short}*" if paper.venue_short else ""
    wanted: dict = {
        "title": paper.title,
        "date": paper.date,
        "publication_types": TYPE_TO_CSL[paper.type],
    }
    if paper.doi:
        wanted["doi"] = paper.doi
    if publication:
        wanted["publication"] = publication
    if short:
        wanted["publication_short"] = short
    if paper.abstract and (refresh or not str(fm.get("abstract") or "").strip()):
        wanted["abstract"] = paper.abstract
    if refresh:
        wanted["authors"] = author_values
    return {k: v for k, v in wanted.items() if not _same(k, fm.get(k), v)}


def match_authors(
    names: list[str], profiles: list["Profile"]
) -> tuple[list[str], list[str]]:
    values, unmatched = [], []
    for name in names:
        slug, ambiguous = match_author(name, profiles)
        values.append(slug or name)
        if not slug:
            unmatched.append(name + (" (ambiguous)" if ambiguous else ""))
    return values, unmatched


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


@dataclass
class Report:
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)
    no_abstract: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def markdown(self) -> str:
        out = ["## Publications sync", ""]
        sections = [
            ("New pages created", self.created),
            ("Existing pages updated", self.updated),
            ("Possible duplicates (nothing written; check by hand)", self.duplicates),
            ("Authors not matched to a profile (kept as plain names)", self.unmatched),
            ("Pages created without an abstract (add one by hand)", self.no_abstract),
            ("Rows with errors", self.errors),
            ("Already on the site", self.skipped),
        ]
        for title, items in sections:
            if items:
                out += [f"### {title}", *[f"- {i}" for i in items], ""]
        if not any(
            [
                self.created,
                self.updated,
                self.duplicates,
                self.unmatched,
                self.no_abstract,
                self.errors,
            ]
        ):
            out.append("No changes.")
        return "\n".join(out) + "\n"


def find_existing(ref: str, ex: Existing) -> str | None:
    """Resolve a DOI, arXiv ID or page slug to an existing page slug."""
    ref = (ref or "").strip()
    if not ref:
        return None
    if ref in ex.slugs:
        return ref
    try:
        kind, norm = classify(ref)
    except ValueError:
        return None
    return ex.dois.get(norm.lower()) if kind == "doi" else ex.arxivs.get(norm)


def similar_preprint(title: str, ex: Existing) -> str | None:
    """Slug of an existing preprint whose title is (nearly) the same."""
    norm = ascii_norm(title)
    best, best_ratio = None, 0.0
    for t, slug in ex.titles.items():
        if ex.types.get(slug) != "article":
            continue
        ratio = difflib.SequenceMatcher(None, norm, t).ratio()
        if ratio > best_ratio:
            best, best_ratio = slug, ratio
    return best if best_ratio >= 0.9 else None


def write_update(folder: Path, updates: dict, bibtex: str, dry_run: bool) -> None:
    if dry_run:
        return
    index = folder / "index.md"
    index.write_text(
        set_keys(index.read_text(encoding="utf-8"), updates), encoding="utf-8"
    )
    if bibtex:
        (folder / "cite.bib").write_text(bibtex, encoding="utf-8")


def describe(slug: str, updates: dict, note: str = "") -> str:
    return f"`{slug}`: {', '.join(updates)}" + (f" ({note})" if note else "")


def process_row(
    row: dict,
    row_no: int,
    ex: Existing,
    profiles: list[Profile],
    out_dir: Path,
    report: Report,
    dry_run: bool,
) -> None:
    label = f"row {row_no}"
    ident = (row.get("id") or "").strip()
    try:
        kind, norm_id = classify(ident)
    except ValueError as exc:
        report.errors.append(f"{label}: {exc}")
        return

    refresh = truthy(row.get("update", ""))
    existing = None
    if kind == "doi":
        existing = ex.dois.get(norm_id.lower())
    elif kind == "arxiv":
        existing = ex.arxivs.get(norm_id)
    replaces = find_existing(row.get("replaces", ""), ex)
    if (row.get("replaces") or "").strip() and not replaces:
        report.errors.append(
            f"{label}: replaces='{row['replaces']}' matches no existing page"
        )
        return

    # Paper already on the site: only sync the sheet-owned fields (and refresh on request).
    if existing and not refresh:
        folder = out_dir / existing
        fm = read_front_matter(folder / "index.md")
        updates = sheet_updates(row, fm)
        if updates:
            report.updated.append(describe(existing, updates, "from the sheet"))
            write_update(folder, updates, "", dry_run)
        else:
            report.skipped.append(f"{label}: {ident} -> `{existing}`")
        return

    # Fetch metadata
    try:
        if kind == "doi":
            paper = fetch_crossref(norm_id)
        elif kind == "arxiv":
            paper = fetch_arxiv(norm_id)
        else:
            paper = Paper()
    except (LookupError, RuntimeError, requests.RequestException, ET.ParseError) as exc:
        report.errors.append(f"{label} ({ident}): {exc}")
        return

    # Manual values override / fill in
    paper.title = (row.get("title") or "").strip() or paper.title
    paper.venue = (row.get("venue") or "").strip() or paper.venue
    paper.venue_short = (row.get("venue_short") or "").strip() or paper.venue_short
    paper.abstract = (row.get("abstract") or "").strip() or paper.abstract
    if (row.get("authors") or "").strip():
        paper.authors = split_list(row["authors"])
    if (row.get("year") or "").strip() and not paper.date:
        paper.date = f"{row['year'].strip()[:4]}-01-01"
    paper.type = (row.get("type") or "").strip().lower() or paper.type

    missing = [
        n
        for n, v in [
            ("title", paper.title),
            ("authors", paper.authors),
            ("date/year", paper.date),
            ("type", paper.type),
        ]
        if not v
    ]
    if missing:
        report.errors.append(
            f"{label} ({ident or paper.title or 'no id'}): missing {', '.join(missing)}; "
            "fill the columns in the sheet"
        )
        return
    if paper.type not in TYPE_TO_CSL:
        report.errors.append(
            f"{label}: type '{paper.type}' must be conference, journal or preprint"
        )
        return

    author_values, unmatched = match_authors(paper.authors, profiles)

    # Is this an update of an existing page?
    #   - explicit refresh of the page for this id (`update` column),
    #   - `replaces` column,
    #   - a published version of an existing preprint (same / very similar title).
    target, note = None, ""
    if existing:
        target, note = existing, "refreshed from " + (ident or "metadata")
    elif replaces:
        target, note = replaces, f"replaced by {ident}"
    else:
        same = ex.titles.get(ascii_norm(paper.title))
        candidate = same or similar_preprint(paper.title, ex)
        if (
            candidate
            and ex.types.get(candidate) == "article"
            and paper.type != "preprint"
        ):
            target, note = candidate, "preprint is now published"
        elif same or slugify(paper.title) in ex.slugs:
            report.duplicates.append(
                f"{label}: '{paper.title}' looks like the existing page "
                f"`{same or slugify(paper.title)}`. Add `replaces` (its DOI, arXiv ID or "
                "folder name) to the row if it is the same paper."
            )
            return

    if target:
        folder = out_dir / target
        fm = read_front_matter(folder / "index.md")
        # A refresh may replace authors; a version upgrade keeps the curated ones.
        updates = metadata_updates(paper, fm, author_values, refresh=bool(existing))
        updates.update(sheet_updates(row, fm))
        if (
            kind == "arxiv"
            and not existing
            and "url_pdf" not in updates
            and not str(fm.get("url_pdf") or "").strip()
        ):
            updates["url_pdf"] = paper.pdf_url
        if not updates:
            report.skipped.append(
                f"{label}: {ident} -> `{target}` (already up to date)"
            )
            return
        report.updated.append(describe(target, updates, note))
        if "authors" in updates and unmatched:
            report.unmatched.append(f"`{target}`: {', '.join(unmatched)}")
        if paper.doi:
            ex.dois[paper.doi.lower()] = target
        if paper.arxiv:
            ex.arxivs[paper.arxiv] = target
        if "publication_types" in updates:
            ex.types[target] = updates["publication_types"]
        write_update(folder, updates, paper.bibtex or build_bibtex(paper), dry_run)
        return

    # New page
    slug = slugify(paper.title)
    if unmatched:
        report.unmatched.append(f"`{slug}`: {', '.join(unmatched)}")
    if not paper.abstract:
        report.no_abstract.append(f"`{slug}`")

    folder = out_dir / slug
    report.created.append(f"`{slug}` ({paper.type}, {paper.date[:4]})")
    ex.slugs.add(slug)
    ex.titles[ascii_norm(paper.title)] = slug
    ex.types[slug] = TYPE_TO_CSL[paper.type]
    if paper.doi:
        ex.dois[paper.doi.lower()] = slug
    if paper.arxiv:
        ex.arxivs[paper.arxiv] = slug
    if dry_run:
        return

    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.md").write_text(
        render_index(paper, author_values, row), encoding="utf-8"
    )
    (folder / "cite.bib").write_text(
        paper.bibtex or build_bibtex(paper), encoding="utf-8"
    )


def _column_name(header: str | None) -> str:
    """'Pdf_url (Optional)' -> 'pdf_url': the sheet may label optional columns."""
    return re.sub(
        r"\s*\(optional\)\s*$", "", (header or "").strip(), flags=re.I
    ).lower()


def read_rows(args: argparse.Namespace) -> list[dict]:
    if args.csv:
        raw = args.csv.read_bytes()
    else:
        sheet_id = os.environ.get("SPAICOM_SHEET_ID")
        gid = os.environ.get("SPAICOM_PUBLICATIONS_GID")
        if not sheet_id or not gid:
            # The publications tab is optional: papers are normally added with
            # `just discover`. Without a tab there is simply nothing to sync.
            print(
                "No publications tab configured (SPAICOM_PUBLICATIONS_GID): nothing to sync."
            )
            return []
        raw = download_sheet_as_csv(sheet_id, int(gid))
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    return [{_column_name(k): (v or "").strip() for k, v in r.items()} for r in reader]


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--csv", type=Path, help="Read rows from a local CSV instead of the sheet."
    )
    ap.add_argument("--output-dir", type=Path, default=PUBLICATION_DIR)
    ap.add_argument("--authors-dir", type=Path, default=AUTHORS_DIR)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be created, write nothing.",
    )
    ap.add_argument(
        "--report", type=Path, help="Also write the Markdown report to this file."
    )
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status 1 if any row had an error.",
    )
    args = ap.parse_args()

    rows = read_rows(args)
    ex = load_existing(args.output_dir)
    profiles = load_profiles(args.authors_dir)
    report = Report()

    for i, row in enumerate(rows, start=2):  # row 1 is the header
        if not any(row.values()):
            continue
        process_row(row, i, ex, profiles, args.output_dir, report, args.dry_run)

    md = report.markdown()
    print(md)
    if args.report:
        args.report.write_text(md, encoding="utf-8")
    if args.strict and report.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
