import sqlite3

def init_db():
    connection = sqlite3.connect('prop_bets.db')
    with open('schema.sql') as f:
        connection.executescript(f.read())
    connection.commit()
    connection.close()
    print("Database initialized.")

if __name__ == '__main__':
    init_db()
