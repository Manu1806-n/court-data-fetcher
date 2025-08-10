# database.py
import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('case_queries.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS queries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  case_type TEXT,
                  case_number TEXT,
                  filing_year TEXT,
                  parties TEXT,
                  filing_date TEXT,
                  next_hearing TEXT,
                  order_link TEXT,
                  timestamp DATETIME)''')
    conn.commit()
    conn.close()

def log_query(case_type, case_number, filing_year, details):
    init_db()
    conn = sqlite3.connect('case_queries.db')
    c = conn.cursor()
    c.execute('''INSERT INTO queries 
                 (case_type, case_number, filing_year, parties, filing_date, next_hearing, order_link, timestamp)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (case_type, case_number, filing_year,
               details.get('parties'),
               details.get('filing_date'),
               details.get('next_hearing'),
               details.get('order_link'),
               datetime.now()))
    conn.commit()
    conn.close()