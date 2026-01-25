import sqlite3
import os
DB='users.db'
print('DB exists:', os.path.exists(DB))
conn=sqlite3.connect(DB)
c=conn.cursor()
print('Tables:')
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table';"):
    print(' -', row[0])

print('\nUsers schema:')
for row in c.execute("PRAGMA table_info(users);"):
    print(row)

print('\nSessions schema:')
for row in c.execute("PRAGMA table_info(sessions);"):
    print(row)

print('\nUser count:')
for row in c.execute("SELECT COUNT(*) FROM users;"):
    print(row[0])

print('\nExisting users (first 5):')
for row in c.execute("SELECT id,email,full_name FROM users LIMIT 5;"):
    print(row)

conn.close()
