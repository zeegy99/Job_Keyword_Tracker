# Job Keyword Scraper
# Scrapes Greenhouse job boards, extracts skill keywords from SWE postings,
# and stores them in Postgres so keyword trends can be tracked over time.

import html
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from postgres.write_to_table import get_connection, write_to_tables

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOARD_TOKENS = ["stripe", "airbnb", "figma", "discord", "robinhood", "coinbase",
              "databricks", "datadog", "reddit"]
KEYWORDS_PATH = Path(__file__).resolve().parent / "software_keywords.json"
JOB_CATEGORY = "Software Engineering"

SWE_PATTERNS = [
    re.compile(r"\bsoftware\s+engineer", re.IGNORECASE),
    re.compile(r"\bswe\b", re.IGNORECASE),
    re.compile(r"\bsoftware\s+developer", re.IGNORECASE),
    re.compile(r"\bfull[\s-]?stack\s+engineer", re.IGNORECASE),
    re.compile(r"\bbackend\s+engineer", re.IGNORECASE),
    re.compile(r"\bfrontend\s+engineer", re.IGNORECASE),
]


# ---------- fetching ----------

def fetch_company_jobs(token: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    try:
        resp = requests.get(url, params={"content": "true"}, timeout=10)
    except requests.RequestException as e:
        print(f"[{token}] request failed: {e}")
        return []
    if resp.status_code != 200:
        print(f"[{token}] HTTP {resp.status_code} — bad board token?")
        return []
    return resp.json().get("jobs", [])


# ---------- keyword matching ----------

def load_keywords(path: Path = KEYWORDS_PATH) -> dict[str, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_patterns(keywords: dict[str, list[str]]) -> dict[str, tuple[str, re.Pattern]]:
    """Maps each term to (category, compiled pattern)."""
    patterns = {}
    for category, terms in keywords.items():
        for term in terms:
            escaped = re.escape(term)
            # \b only works next to word characters, so skip it around C++, C#, etc.
            left = r"\b" if term[0].isalnum() else ""
            right = r"\b" if term[-1].isalnum() else ""
            patterns[term] = (category, re.compile(f"{left}{escaped}{right}", re.IGNORECASE))
    return patterns


def match_keywords(text: str, patterns: dict[str, tuple[str, re.Pattern]]) -> set[tuple[str, str]]:
    """Returns {(keyword, category), ...} found at least once in text."""
    return {(term, cat) for term, (cat, pat) in patterns.items() if pat.search(text)}


def is_swe_title(title: str) -> bool:
    return any(p.search(title) for p in SWE_PATTERNS)


# ---------- parsing ----------

def parse_html(content: str | None) -> str:
    if not content or not content.strip():
        return ""
    real_html = html.unescape(content)  # Greenhouse double-encodes: &lt;h2&gt; -> <h2>
    soup = BeautifulSoup(real_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


# ---------- main loop ----------

def scrape_board(conn, token: str, patterns) -> tuple[int, int]:
    """Returns (new_jobs, duplicate_jobs) for this board."""
    new, dupes = 0, 0
    scraped_at = date.today()

    for job in fetch_company_jobs(token):
        if not is_swe_title(job["title"]):
            continue

        text = parse_html(job.get("content"))
        keyword_pairs = match_keywords(text, patterns)

        is_new = write_to_tables(
            conn,
            job_id=job["id"],
            company=token,
            title=job["title"],
            job_category=JOB_CATEGORY,
            date_posted=job["first_published"],
            scraped_at=scraped_at,
            url=job["absolute_url"],
            keyword_pairs=keyword_pairs,
        )

        if is_new:
            new += 1
            print(f"[{token}] new: {job['title']} ({len(keyword_pairs)} keywords)")
        else:
            dupes += 1

    return new, dupes


def main():
    patterns = build_patterns(load_keywords())
    conn = get_connection()
    try:
        for token in BOARD_TOKENS:
            new, dupes = scrape_board(conn, token, patterns)
            print(f"[{token}] done: {new} new, {dupes} already stored")
            time.sleep(0.5)
    finally:
        conn.close()


if __name__ == "__main__":
    main()