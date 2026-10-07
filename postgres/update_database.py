import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")



def adding_row():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("ALTER TABLE jobs ADD COLUMN inUSA BOOLEAN DEFAULT false;")

    conn.commit()
    cursor.close()
    conn.close()

# adding_row()
def check_columns():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    exe = "SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'jobs' ORDER BY ordinal_position;"
    cursor.execute(exe)

    rows = cursor.fetchall()
    print(rows)
    cursor.close()
    conn.close()

if __name__ == "__main__":
    # adding_row()
    check_columns()
    