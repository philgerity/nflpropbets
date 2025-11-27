import os
import psycopg2

# Initialize PostgreSQL database with schema
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    exit(1)

print("Connecting to PostgreSQL database...")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

print("Reading schema...")
with open('schema_postgres.sql', 'r') as f:
    schema = f.read()

print("Creating tables...")
cursor.execute(schema)
conn.commit()

print("Database initialized successfully!")
cursor.close()
conn.close()
