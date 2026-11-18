#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
#     "requests",
#     "textual>=0.80",
# ]
# ///
"""
Find papers of lab members that are not on the site yet, and let a human pick which
ones to add.

    uv run scripts/discover_papers.py                       # all active members
    uv run scripts/discover_papers.py --member paolo-di-lorenzo
    uv run scripts/discover_papers.py --list                # print candidates, no TUI

How it works
  1. Members come from content/authors/ (those with `active: false` are skipped; set it
     in the "People" sheet). Each member is matched once to an OpenAlex author ID,
     saved in discovery/openalex_ids.csv.
  2. OpenAlex lists the member's works published since `since` (discovery/discovery.toml).
  3. A candidate is hidden when it is already on the site, was reviewed before
     (discovery/papers_reviewed.csv) or breaks a rule (for example "Barbarossa or
     Di Lorenzo must be a co-author"; rules can be switched off in the TUI with `r`).
  4. In the TUI you mark each paper: add, add as featured or discard. Applying creates
     the pages with the same code as the sheet sync (scripts/sync_publications.py) and
     records every decision in discovery/papers_reviewed.csv, so nothing is asked twice.

Nothing is committed: review the changes with git and commit them yourself.
"""

import argparse
import csv
import os
import sys
import tomllib
import urllib.parse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync_publications as sp

OPENALEX = "https://api.openalex.org"
DATA = Path("discovery")
IDS_FILE = DATA / "openalex_ids.csv"
REVIEWED_FILE = DATA / "papers_reviewed.csv"
CONFIG_FILE = DATA / "discovery.toml"

DEFAULT_CONFIG = """\
# Settings for scripts/discover_papers.py

# Only list papers published on or after this date (avoids a member's whole career).
since = "2023-01-01"

# A paper is listed only if at least one of these people is a co-author
# (profile folder names in content/authors/). Use [] to disable the rule.
# In the TUI, press `r` to temporarily show papers that fail the rule.
require_any_coauthor = []
"""


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    id: str  # DOI or arXiv ID, as accepted by sync_publications
    title: str
    date: str
    venue: str
    kind: str  # OpenAlex work type
    authors: list[str]
    members: list[str]  # lab members (slugs) who are authors of this paper
    rule_ok: bool = True
    note: str = ""  # e.g. "published version of `some-preprint`"
    status: str = "pending"  # pending | add | featured | discard

    @property
    def year(self) -> str:
        return self.date[:4]


@dataclass
class Config:
    since: str = "2023-01-01"
    require_any_coauthor: list[str] = field(default_factory=list)


def load_config(path: Path) -> Config:
    if not path.exists():
        return Config()
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return Config(
        since=str(data.get("since", "2023-01-01")),
        require_any_coauthor=list(data.get("require_any_coauthor", [])),
    )


# ---------------------------------------------------------------------------
# Review state (CSV, so that git diffs are readable)
# ---------------------------------------------------------------------------


def read_reviewed(path: Path) -> tuple[set[str], set[str]]:
    """Return (ids, normalized titles) that were reviewed before."""
    ids, titles = set(), set()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                ids.add((row.get("id") or "").strip().lower())
                if row.get("title"):
                    titles.add(sp.ascii_norm(row["title"]))
    return ids, titles


def append_reviewed(path: Path, entries: list[tuple[str, str, str]]) -> None:
    """entries: (id, status, title)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["id", "status", "date", "title"])
        for ident, status, title in entries:
            w.writerow([ident, status, date.today().isoformat(), title])


def read_ids(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                out[row["slug"]] = row["openalex_id"]
    return out


def write_ids(path: Path, ids: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["slug", "openalex_id"])
        for slug in sorted(ids):
            w.writerow([slug, ids[slug]])


# ---------------------------------------------------------------------------
# OpenAlex
# ---------------------------------------------------------------------------


def _oa_get(path: str, params: dict) -> dict:
    mailto = os.environ.get("CROSSREF_MAILTO")
    if mailto:
        params = {**params, "mailto": mailto}
    query = urllib.parse.urlencode(params, safe=":,|*")
    resp = sp.http_get(f"{OPENALEX}/{path}?{query}")
    if resp.status_code != 200:
        raise RuntimeError(f"OpenAlex {path}: HTTP {resp.status_code}")
    return resp.json()


def search_author(name: str) -> list[dict]:
    return _oa_get("authors", {"search": name, "per-page": 6}).get("results", [])


def short_id(openalex_url: str) -> str:
    return openalex_url.rsplit("/", 1)[-1]


def fetch_works(author_id: str, since: str) -> list[dict]:
    works, cursor = [], "*"
    while cursor:
        data = _oa_get(
            "works",
            {
                "filter": f"author.id:{author_id},from_publication_date:{since}",
                "per-page": 100,
                "cursor": cursor,
                "select": "id,doi,title,publication_date,type,primary_location,authorships",
            },
        )
        works += data.get("results", [])
        cursor = (data.get("meta") or {}).get("next_cursor")
        if not data.get("results"):
            break
    return works


# ---------------------------------------------------------------------------
# Building the candidate list
# ---------------------------------------------------------------------------


def active_members(authors_dir: Path, only: list[str] | None) -> list[sp.Profile]:
    out = []
    for p in sp.load_profiles(authors_dir):
        fm = sp.read_front_matter(authors_dir / p.slug / "_index.md")
        if fm.get("active") is False:
            continue
        if only and p.slug not in only:
            continue
        out.append(p)
    return out


def resolve_ids(
    members: list[sp.Profile], ids: dict[str, str], ids_file: Path
) -> dict[str, str]:
    """Ask once per member which OpenAlex author is them; remember the answer."""
    changed = False
    for p in members:
        if p.slug in ids:
            continue
        name = f"{p.first} {p.last}"
        if not sys.stdin.isatty():
            print(f"  {name}: no OpenAlex ID yet (run interactively to choose one)")
            continue
        print(f"\nWhich OpenAlex author is {name}?")
        try:
            found = search_author(name)
        except RuntimeError as exc:
            print(f"  search failed: {exc}")
            continue
        for i, a in enumerate(found, 1):
            inst = ", ".join(
                x.get("display_name", "")
                for x in a.get("last_known_institutions") or []
            )
            print(
                f"  {i}) {a['display_name']}  [{short_id(a['id'])}]  "
                f"{a.get('works_count', 0)} works  {inst or '-'}"
            )
            topics = ", ".join(t["display_name"] for t in (a.get("topics") or [])[:3])
            print(f"     topics: {topics or '-'}")
        ans = input("  number, an ID like A5012345678, or s to skip for now: ").strip()
        if ans.isdigit() and 1 <= int(ans) <= len(found):
            ids[p.slug] = short_id(found[int(ans) - 1]["id"])
            changed = True
        elif ans.upper().startswith("A") and ans[1:].isdigit():
            ids[p.slug] = ans.upper()
            changed = True
    if changed:
        write_ids(ids_file, ids)
    return ids


def build_candidates(
    members: list[sp.Profile],
    ids: dict[str, str],
    cfg: Config,
    ex: sp.Existing,
    profiles: list[sp.Profile],
    reviewed: tuple[set[str], set[str]],
    log=print,
) -> list[Candidate]:
    rev_ids, rev_titles = reviewed
    by_key: dict[str, Candidate] = {}
    for m in members:
        aid = ids.get(m.slug)
        if not aid:
            continue
        log(f"  fetching {m.first} {m.last} ({aid})")
        for w in fetch_works(aid, cfg.since):
            doi = w.get("doi")
            title = (w.get("title") or "").strip()
            if not doi or not title:
                continue  # cannot be turned into a page automatically
            try:
                kind, norm = sp.classify(doi)
            except ValueError:
                continue
            ident = norm
            key = ident.lower()
            if key in by_key:
                if m.slug not in by_key[key].members:
                    by_key[key].members.append(m.slug)
                continue
            names = [
                (a.get("author") or {}).get("display_name", "")
                for a in w.get("authorships", [])
            ]
            src = ((w.get("primary_location") or {}).get("source") or {}).get(
                "display_name", ""
            ) or ""
            by_key[key] = Candidate(
                id=ident,
                title=title,
                date=w.get("publication_date") or "",
                venue=src,
                kind=w.get("type") or "",
                authors=[n for n in names if n],
                members=[m.slug],
            )

    out: list[Candidate] = []
    for c in sorted(by_key.values(), key=lambda c: c.date, reverse=True):
        kind, norm = sp.classify(c.id)
        norm_title = sp.ascii_norm(c.title)
        if c.id.lower() in rev_ids or norm_title in rev_titles:
            continue
        slug = ex.dois.get(norm.lower()) if kind == "doi" else ex.arxivs.get(norm)
        if slug:
            continue  # already on the site
        same = ex.titles.get(norm_title) or sp.similar_preprint(c.title, ex)
        if same:
            if kind == "doi" and ex.types.get(same) == "article":
                c.note = f"published version of preprint `{same}` (updates it)"
            else:
                continue  # same paper under another identifier
        if cfg.require_any_coauthor:
            slugs = {
                s
                for n in c.authors
                if (s := sp.match_author(n, profiles)[0]) is not None
            }
            c.rule_ok = bool(slugs & set(cfg.require_any_coauthor))
        out.append(c)
    return out


# ---------------------------------------------------------------------------
# Applying the decisions
# ---------------------------------------------------------------------------


def apply_decisions(
    cands: list[Candidate],
    out_dir: Path,
    authors_dir: Path,
    reviewed_file: Path,
    dry_run: bool = False,
    log=print,
) -> sp.Report:
    ex = sp.load_existing(out_dir)
    profiles = sp.load_profiles(authors_dir)
    report = sp.Report()
    entries: list[tuple[str, str, str]] = []
    todo = [c for c in cands if c.status in ("add", "featured")]
    log(
        f"Applying: {len(todo)} to add, {sum(c.status == 'discard' for c in cands)} to discard."
    )
    for n, c in enumerate(cands, 1):
        if c.status in ("add", "featured"):
            log(f"  fetching and writing: {c.title[:70]} ...")
            before = len(report.errors) + len(report.duplicates)
            row = {"id": c.id, "featured": "yes" if c.status == "featured" else ""}
            sp.process_row(row, n, ex, profiles, out_dir, report, dry_run)
            if len(report.errors) + len(report.duplicates) == before:
                entries.append((c.id, "added", c.title))
        elif c.status == "discard":
            entries.append((c.id, "discarded", c.title))
    if entries and not dry_run:
        append_reviewed(reviewed_file, entries)
    return report


# ---------------------------------------------------------------------------
# TUI
# ---------------------------------------------------------------------------

MARK = {"pending": " ", "add": "+", "featured": "★", "discard": "✕"}


def make_app(cands: list[Candidate], cfg: Config):
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.widgets import DataTable, Footer, Header, Static

    class Discover(App):
        TITLE = "SPAICOM: new papers"
        CSS = """
        DataTable { height: 1fr; }
        #detail { height: 8; padding: 0 1; border-top: solid $accent; }
        """
        BINDINGS: ClassVar = [
            Binding("a", "mark('add')", "Add"),
            Binding("f", "mark('featured')", "Add+featured"),
            Binding("d", "mark('discard')", "Discard"),
            Binding("u", "mark('pending')", "Undo"),
            Binding("r", "toggle_rules", "Rules on/off"),
            Binding("w", "save", "Apply & save"),
            Binding("q", "quit_app", "Quit"),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.rules_on = bool(cfg.require_any_coauthor)
            self._quit_armed = False

        # -- helpers
        def visible(self) -> list[Candidate]:
            return [c for c in cands if c.rule_ok or not self.rules_on]

        def compose(self) -> ComposeResult:
            yield Header()
            yield DataTable(cursor_type="row", zebra_stripes=True)
            yield Static("", id="detail")
            yield Footer()

        def on_mount(self) -> None:
            t = self.query_one(DataTable)
            t.add_columns("", "Year", "Title", "Venue", "Members")
            self.refresh_table()

        def refresh_table(self) -> None:
            t = self.query_one(DataTable)
            t.clear()
            for c in self.visible():
                title = c.title if len(c.title) <= 70 else c.title[:67] + "..."
                flag = "" if c.rule_ok else " ⚠"
                t.add_row(
                    MARK[c.status],
                    c.year,
                    title + flag,
                    c.venue[:30],
                    ", ".join(c.members),
                    key=c.id,
                )
            self.sub_title = self.summary()
            self.show_detail()

        def summary(self) -> str:
            n = lambda s: sum(1 for c in cands if c.status == s)
            hidden = sum(1 for c in cands if not c.rule_ok) if self.rules_on else 0
            rules = "rules ON" if self.rules_on else "rules OFF"
            return (
                f"{len(self.visible())} shown ({hidden} hidden by rules, {rules}) | "
                f"add {n('add')}  featured {n('featured')}  discard {n('discard')}"
            )

        def current(self) -> Candidate | None:
            t = self.query_one(DataTable)
            rows = self.visible()
            if not rows or t.cursor_row is None or t.cursor_row >= len(rows):
                return None
            return rows[t.cursor_row]

        def show_detail(self) -> None:
            c = self.current()
            box = self.query_one("#detail", Static)
            if c is None:
                box.update("Nothing to review.")
                return
            lines = [
                f"[b]{c.title}[/b]",
                f"{c.date}  |  {c.kind}  |  {c.venue or '-'}",
                f"id: {c.id}",
                "authors: "
                + ", ".join(c.authors[:12])
                + (" ..." if len(c.authors) > 12 else ""),
            ]
            if c.note:
                lines.append(f"[yellow]{c.note}[/yellow]")
            if not c.rule_ok:
                lines.append("[red]fails the co-author rule[/red]")
            box.update("\n".join(lines))

        # -- events / actions
        def on_data_table_row_highlighted(self, _event) -> None:
            self.show_detail()

        def action_mark(self, status: str) -> None:
            c = self.current()
            if c is None:
                return
            c.status = status
            t = self.query_one(DataTable)
            row = t.cursor_row
            t.update_cell_at((row, 0), MARK[status])
            self.sub_title = self.summary()
            if status != "pending" and row + 1 < len(self.visible()):
                t.move_cursor(row=row + 1)

        def action_toggle_rules(self) -> None:
            if not cfg.require_any_coauthor:
                self.notify(
                    "No co-author rule is configured (discovery/discovery.toml)."
                )
                return
            self.rules_on = not self.rules_on
            self.refresh_table()

        def action_save(self) -> None:
            self.exit(True)

        def action_quit_app(self) -> None:
            marked = any(c.status != "pending" for c in cands)
            if marked and not self._quit_armed:
                self._quit_armed = True
                self.notify("Decisions not applied. Press q again to quit, w to apply.")
                return
            self.exit(False)

    return Discover()


# ---------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--member", action="append", help="Only this profile slug (repeatable)."
    )
    ap.add_argument(
        "--since", help="Override `since` from discovery/discovery.toml (YYYY-MM-DD)."
    )
    ap.add_argument(
        "--list", action="store_true", help="Print candidates and exit (no TUI)."
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="Apply without writing files."
    )
    ap.add_argument("--config", type=Path, default=CONFIG_FILE)
    ap.add_argument("--ids-file", type=Path, default=IDS_FILE)
    ap.add_argument("--reviewed-file", type=Path, default=REVIEWED_FILE)
    ap.add_argument("--output-dir", type=Path, default=sp.PUBLICATION_DIR)
    ap.add_argument("--authors-dir", type=Path, default=sp.AUTHORS_DIR)
    args = ap.parse_args()

    if not args.config.exists():
        args.config.parent.mkdir(parents=True, exist_ok=True)
        args.config.write_text(DEFAULT_CONFIG, encoding="utf-8")
        print(f"Created {args.config}; edit it to set the date and the co-author rule.")
    cfg = load_config(args.config)
    if args.since:
        cfg.since = args.since

    profiles = sp.load_profiles(args.authors_dir)
    unknown = [
        s for s in cfg.require_any_coauthor if s not in {p.slug for p in profiles}
    ]
    if unknown:
        sys.exit(
            f"{args.config}: unknown profile(s) in require_any_coauthor: {unknown}"
        )
    members = active_members(args.authors_dir, args.member)
    if not members:
        sys.exit("No active members found.")

    ids = resolve_ids(members, read_ids(args.ids_file), args.ids_file)
    ex = sp.load_existing(args.output_dir)
    cands = build_candidates(
        members, ids, cfg, ex, profiles, read_reviewed(args.reviewed_file)
    )
    shown = [c for c in cands if c.rule_ok]
    print(
        f"\n{len(shown)} new paper(s) to review ({len(cands) - len(shown)} hidden by rules)."
    )

    if args.list or not cands:
        for c in cands:
            flag = "" if c.rule_ok else "  [fails rule]"
            print(
                f"- {c.date} {c.id}  {c.title}{flag}"
                + (f"  ({c.note})" if c.note else "")
            )
        return
    if not sys.stdout.isatty():
        sys.exit("The review screen needs a terminal; use --list to just print.")

    print(
        "Opening the review screen (the first start can take a few seconds)...",
        flush=True,
    )
    if not make_app(cands, cfg).run():
        print("Nothing applied.")
        return
    report = apply_decisions(
        cands, args.output_dir, args.authors_dir, args.reviewed_file, args.dry_run
    )
    print(report.markdown())
    print(
        "Review with `git status`, run `just check`, then commit "
        "(content/publication/ and discovery/papers_reviewed.csv)."
    )


if __name__ == "__main__":
    main()
