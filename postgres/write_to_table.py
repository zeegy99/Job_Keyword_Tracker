import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def write_to_jobs_table(id, company, title, job_category, date_posted, scraped_at, url):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    insert_query = "INSERT INTO jobs (id, company, title, job_category, date_posted, scraped_at, url) values (%s, %s, %s, %s, %s, %s, %s); "
    data_to_insert = (id, company, title, job_category, date_posted, scraped_at, url)

    cursor.execute(insert_query, data_to_insert)

    conn.commit()

    cursor.close()
    conn.close()

def write_to_job_keywords_table(job_id, keyword, category):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    insert_query = "INSERT INTO job_keywords (job_id, keyword, category) values (%s, %s, %s)"
    data_to_insert = (job_id, keyword, category)
    cursor.execute(insert_query, data_to_insert)
    conn.commit()
    cursor.close()
    conn.close()

def write_to_tables(id, company, title, job_category, date_posted, scraped_at, url, keywords, category):

    write_to_jobs_table(id, company, title, job_category, date_posted, scraped_at, url)
    for keyword in keywords:
        write_to_job_keywords_table(id, keyword, category)


    

