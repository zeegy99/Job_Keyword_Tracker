import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def write_to_jobs_table(cursor, job_id, company, title, job_category,
                        date_posted, scraped_at, url):
    
    cursor.execute("""
        INSERT INTO jobs (id, company, title, job_category, date_posted, scraped_at, url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        RETURNING id
    """, (job_id, company, title, job_category, date_posted, scraped_at, url))
    return cursor.fetchone() is not None


def write_to_job_keywords_table(cursor, job_id, keyword_pairs):
   
    rows = [(job_id, kw, cat) for kw, cat in keyword_pairs]
    if not rows:
        return
    execute_values(cursor, """
        INSERT INTO job_keywords (job_id, keyword, category)
        VALUES %s
        ON CONFLICT DO NOTHING
    """, rows)


def write_to_tables(conn, job_id, company, title, job_category,
                    date_posted, scraped_at, url, keyword_pairs):

    
    with conn:                          
        with conn.cursor() as cursor:   
            is_new = write_to_jobs_table(cursor, job_id, company, title,
                                         job_category, date_posted, scraped_at, url)
            if not is_new:
                return False
            write_to_job_keywords_table(cursor, job_id, keyword_pairs)
    return True