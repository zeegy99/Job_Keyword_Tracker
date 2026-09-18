import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

    
def create_jobs_table():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS jobs(" \
    "id BIGINT PRIMARY KEY," \
    "company TEXT NOT NULL," \
    "title TEXT NOT NULL," \
    "job_category TEXT NOT NULL," \
    "date_posted DATE NOT NULL," \
    "scraped_at TIMESTAMPTZ NOT NULL DEFAULT now()," \
    "url TEXT)")

    conn.commit()

    cursor.close()
    conn.close()

def create_jobKeywords_table():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS job_keywords ("
        "job_id BIGINT REFERENCES jobs(id),"
        "keyword TEXT NOT NULL,"
        "category TEXT NOT NULL,"
        "PRIMARY KEY (job_id, keyword))"
    )

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    # create_database('job_tracker')
    create_jobKeywords_table()