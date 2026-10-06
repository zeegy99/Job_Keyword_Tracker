# Job Keyword Scraper
# Scrapes Greenhouse job boards, extracts skill keywords from SWE postings,
# and stores them in Postgres so keyword trends can be tracked over time.

import html
import json
import os
import re
import smtplib
import sys
import time
from datetime import date
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from postgres.write_to_table import get_connection, write_to_tables

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BOARD_TOKENS = ["stripe", "airbnb", "figma", "discord", "robinhood", "coinbase",
              "databricks", "datadog", "reddit", "SpaceX", "Carvana"]
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

# ---------- new grad filter ----------

MAX_YEARS_EXPERIENCE = 1

NEW_GRAD_PATTERN = re.compile(
    r"\bnew\s+grad|\brecent\s+grad|\buniversity\s+grad|\bearly[\s-]career\b"
    r"|\bentry[\s-]level\b|\bjunior\b|\bengineer\s+I\b(?!I)",
    re.IGNORECASE,
)
EXCLUDE_TITLE_PATTERN = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|manager|director|architect|intern|internship)\b"
    r"|\bengineer\s+(II|III|IV)\b",
    re.IGNORECASE,
)
# "3+ years of experience", "0-2 years of professional experience", "5 years experience"
YEARS_PATTERN = re.compile(
    r"(\d{1,2})\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*\d{1,2}\s*)?\+?\s*years?\s+(?:of\s+)?(?:[\w-]+\s+){0,3}experience",
    re.IGNORECASE,
)


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


def min_years_required(text: str) -> int | None:
    """Smallest 'N years of experience' mentioned, or None if not stated."""
    years = [int(m.group(1)) for m in YEARS_PATTERN.finditer(text)]
    return min(years) if years else None


def is_new_grad(title: str, text: str) -> bool:
    if EXCLUDE_TITLE_PATTERN.search(title):
        return False
    years = min_years_required(text)
    if years is not None and years > MAX_YEARS_EXPERIENCE:
        return False
    # No explicit new grad wording: only accept if the posting states a low bar.
    return bool(NEW_GRAD_PATTERN.search(title) or NEW_GRAD_PATTERN.search(text)) or years is not None


# ---------- parsing ----------

def parse_html(content: str | None) -> str:
    if not content or not content.strip():
        return ""
    real_html = html.unescape(content)  # Greenhouse double-encodes: &lt;h2&gt; -> <h2>
    soup = BeautifulSoup(real_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


# ---------- notifications ----------

def send_email(jobs: list[dict]) -> None:
    """Emails a digest of new grad jobs to myself via Gmail SMTP """
    sender = "fred.yuan392@gmail.com"
    password = os.getenv("EMAIL_APP_PASSWORD")
    recipient = "fred.yuan392@gmail.com"

    if not sender or not password:
            print("EMAIL_ADDRESS / EMAIL_APP_PASSWORD not set — skipping email")
            return
    #In the future, I will make it so that you can add youself to the recipient list

    
    

    msg = EmailMessage()
    msg["Subject"] = f"{len(jobs)} new grad SWE job(s) — {date.today():%b %d}"
    msg["From"] = sender
    msg["To"] = recipient

    if not jobs:
        print("No qualifying jobs found")
        msg.set_content("No new jobs found today")
    else:
        msg.set_content("\n\n".join(f"{j['company']}: {j['title']}\n{j['url']}" for j in jobs))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)
    print(f"Emailed {len(jobs)} new grad job(s) to {recipient}")



# ---------- main loop ----------

def scrape_board(conn, token: str, patterns) -> tuple[int, int, list[dict]]:
    """Returns (new_jobs, duplicate_jobs, new_grad_matches) for this board."""
    new, dupes = 0, 0
    matches = []
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
            if is_new_grad(job["title"], text):
                matches.append({"company": token, "title": job["title"], "url": job["absolute_url"]})
        else:
            dupes += 1

    return new, dupes, matches


def main():
    patterns = build_patterns(load_keywords())
    conn = get_connection()
    all_matches = []
    try:
        for token in BOARD_TOKENS:
            new, dupes, matches = scrape_board(conn, token, patterns)
            all_matches.extend(matches)
            print(f"[{token}] done: {new} new, {dupes} already stored, {len(matches)} new grad")
            time.sleep(0.5)
    finally:
        conn.close()
    send_email(all_matches)


if __name__ == "__main__":
    main()