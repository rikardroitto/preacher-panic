import psycopg2
from datetime import datetime, timedelta
import socket

# Force IPv4
socket.AF_INET6 = socket.AF_INET

DATABASE_URL = 'postgresql://postgres:5N!u_CBidqhME3A@db.uteqluwrvccmyqucvset.supabase.co:5432/postgres'

# Seed data
scores = [
    ("Prisad vare Admin!", 79, 7*60+57),
    ("rraaaaaaahghghhhh", 66, 6*60+44),
    ("Preaching is hard", 30, 2*60+38),
    ("Andréas", 25, 3*60+22),
    ("Stärkt till medveten", 17, 1*60+45),
    ("Gil", 14, 1*60+42),
    ("Gil", 4, 0*60+40),
    ("Drake", 3, 0*60+53),
    ("Predikoutkastaren", 3, 1*60+1),
    ("Stärkt", 2, 0*60+48),
]

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# Clear existing data
cur.execute("DELETE FROM leaderboard")

# Insert scores with varied timestamps
today = datetime.now().date()
for i, (name, words, time_sec) in enumerate(scores):
    # Spread entries over the last few days
    date = today - timedelta(days=i % 3)
    timestamp = datetime.now() - timedelta(days=i % 3, hours=i)

    cur.execute('''
        INSERT INTO leaderboard (name, words_collected, time, created_at, date)
        VALUES (%s, %s, %s, %s, %s)
    ''', (name, words, time_sec, timestamp, date))

conn.commit()
cur.close()
conn.close()

print("✅ Leaderboard seeded successfully!")
