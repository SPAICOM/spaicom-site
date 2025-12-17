"""
Utility module for downloading Google Sheets data as CSV.

This module provides helper functions to retrieve the contents of a
specific worksheet ("foglio") from a Google Sheets document using the
public CSV export endpoint.

Available functions
-------------------
- download_sheet_as_csv(gsheet_id: str, gid: int) -> bytes
    Download a specific worksheet from a Google Sheets document as CSV
    and return its raw bytes.
"""

import requests


def download_sheet_as_csv(
    gsheet_id: str,
    gid: int,
) -> bytes:
    """
    Download a specific worksheet (foglio) from a Google Sheets document as CSV.

    The function builds the Google Sheets CSV export URL using the provided
    spreadsheet ID and worksheet GID, performs an HTTP GET request, and
    returns the raw CSV content.

    Parameters
    ----------
    gsheet_id : str
    The ID of the Google Sheets document (the long identifier in the URL).
    gid : int
    The numeric GID of the worksheet (foglio) within the spreadsheet.

    Returns
    -------
    bytes
    The raw CSV content of the requested worksheet.

    Raises
    ------
    requests.HTTPError
    If the HTTP request fails or returns a non-success status code.

    Notes
    -----
    - The Google Sheet must be publicly accessible or otherwise readable
    without authentication for this method to work.
    - The returned value is raw bytes; decode it (e.g., using UTF-8) if a
    string representation is required.
    """
    csv_url = f"https://docs.google.com/spreadsheets/d/{gsheet_id}/export?format=csv&gid={gid}"

    print(f"Downloading foglio gid={gid} from:\n{csv_url}")
    resp = requests.get(csv_url)
    resp.raise_for_status()
    return resp.content


if __name__ == "__main__":
    pass
