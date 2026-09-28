#The goal is that you will search something like "Software Engineer"

#And this will scrape through n job postings and output what keywords are most searched. 

#We can automatically search once per day, track keywords in a database and potentially graph how requirements
#Slowly shift

import requests
import time
import sys
from pprint import pprint
from datetime import datetime, date
from bs4 import BeautifulSoup
import re
import json
import html
import os 
import psycopg2
import os 
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
from pathlib import Path 
working_dir = str(Path(__file__).resolve().parent.parent)
sys.path.append(working_dir)

from postgres.write_to_table import write_to_tables


# import write_to_table

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BOARD_TOKENS = ["stripe", "meta"]  

def fetch_company_jobs(token) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
    resp = requests.get(url, params={"content": "true"}, timeout=10)
    if resp.status_code != 200:
        return []
    return resp.json().get("jobs", [])

date_format = '%Y-%m-%d'

def load_keywords(path = 'software_keywords.json'):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_patterns(keywords: dict[str, list[str]]) -> dict[str, re.Pattern]:

    patterns = {}
    for category, terms in keywords.items():
        for term in terms:
    
            escaped = re.escape(term)
     
            left = r'\b' if term[0].isalnum() else ''
            right = r'\b' if term[-1].isalnum() else ''
            pattern = re.compile(f'{left}{escaped}{right}', re.IGNORECASE)
            patterns[term] = pattern
    return patterns

def match_keywords(text: str, patterns: dict[str, re.Pattern]) -> set[str]:
    """Returns the set of keywords found at least once in this text."""
    found = set()
    for term, pattern in patterns.items():
        if pattern.search(text):
            found.add(term)
    return found

SWE_PATTERNS = [
    re.compile(r'\bsoftware\s+engineer', re.IGNORECASE),
    re.compile(r'\bswe\b', re.IGNORECASE),
    re.compile(r'\bsoftware\s+developer', re.IGNORECASE),
    re.compile(r'\bfull[\s-]?stack\s+engineer', re.IGNORECASE),
    re.compile(r'\bbackend\s+engineer', re.IGNORECASE),
    re.compile(r'\bfrontend\s+engineer', re.IGNORECASE),
]

def is_swe_title(title: str) -> bool:
    return any(pattern.search(title) for pattern in SWE_PATTERNS)





# print(patterns)

def stripe_datetime(s): #Convert All Datetimes into '%Y-%m-%d'
    correct_datetime = s[:s.find('T')]
    datetime_obj = datetime.strptime(correct_datetime, date_format)
    return datetime_obj

def date_in_range(input_date, start = date(2026, 9, 20), end = date.today()):
    # print(type(input_date), type(start), type(end)) #input date is a datetime.datetime, everything else is a datetime.date
    if input_date.date() >= start and input_date.date() <= end:
        return True
    return False

def get_desc(content):
    return content.find('What you’ll do')

def get_min_requirements(content):
    return content.find('Minimum requirements')

def get_preferred_requirements(content):
    return content.find('Preferred qualifications')

def filter_content(content):
    desc = get_desc(content)
    min_req = get_min_requirements(content)
    pref_req = get_preferred_requirements(content)

    company_yap = content[:desc]
    what_you_do = content[desc:min_req]
    minimum_requirements = content[min_req:pref_req]
    prefered_requirements = content[pref_req:]

    return parse_html(company_yap), parse_html(what_you_do), parse_html(minimum_requirements), parse_html(prefered_requirements), parse_html(content)

def parse_html(content: str | None) -> str:
    if not content or not content.strip():
        return ""
    real_html = html.unescape(content)   # &lt;h2&gt; -> <h2>, actual tags now
    soup = BeautifulSoup(real_html, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def get_information(job):
    id = job['id']
    company = job['company_name']
    title = job['title']
    job_category = 'Software Engineering'
    date_posted = job['first_published']
    scraped_at = date.today()
    url = job['absolute_url']
    
    category = 'Software Engineering'
    
    yap, desc, min, pref, all = filter_content(job['content'])
    found = match_keywords(all, patterns)

    keywords = found
    return (id, company, title, job_category, date_posted, scraped_at, url, keywords, category)

patterns = build_patterns(load_keywords())
all_jobs = []
filtered = []

conn = psycopg2.connect(DATABASE_URL)
def find_job():
    for token in BOARD_TOKENS:
        jobs = fetch_company_jobs(token)
        for job in jobs:
            if is_swe_title(job['title']):
                datetime_obj = stripe_datetime(job['first_published'])
                job["_company_token"] = token
                if date_in_range(datetime_obj):
                    
                    
                    (id, company, title, job_category, date_posted, scraped_at, url, keywords, category) = get_information(job)
                
                    try: 
                        write_to_tables(conn, id, company, title, job_category, date_posted, scraped_at, url, keywords, category)
                    
                    finally:
                        conn.close()
                


        all_jobs.extend(jobs)
        time.sleep(0.5) 


find_job()

    
