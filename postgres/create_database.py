
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def verification():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("SELECT version()")

    result = cursor.fetchall()

    print(result)

    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")

    result = cursor.fetchall()
    print(result)
    cursor.close
    conn.close
    return 200

def check_if_database_exists(database_name):
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    cursor.execute("SELECT datname FROM pg_database WHERE datname = %s", (database_name,))

    result = cursor.fetchall()
    cursor.close()
    conn.close()

    if result:
        return True
    return False


def create_database(database_name):
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    if not check_if_database_exists(database_name):
        cursor.execute("CREATE DATABASE %s", (database_name,))
    else:
        print(f"Database {database_name} already exists")
        return False
    
    cursor.execute("SELECT datname FROM pg_database WHERE datname = %s", (database_name,))
    result = cursor.fetchall()
    cursor.close
    conn.close
    if result:
        print(f"Successfully created database {database_name}")
        return True
    else:
        print("Failed to create database")
        return False
