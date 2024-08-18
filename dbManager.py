import sqlite3
import threading


class DB:
    def __init__(self):

        self.db = sqlite3.connect("saved.db", check_same_thread=False)
        self.cursor = self.db.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                url TEXT PRIMARY KEY
            )
            """
        )
        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_url ON urls(url);
            """
        )
        self.db.commit()

        self.db.execute("PRAGMA journal_mode=WAL;")
        self.lock = threading.Lock()

    def insert(self, url):

        with self.lock:
            self.cursor.execute("INSERT INTO urls (url) VALUES (?)", (url[13:],))
            self.db.commit()

    def urlSaved(self, url):
        with self.lock:
            self.cursor.execute("SELECT 1 FROM urls WHERE url = ?", (url,))
            return self.cursor.fetchone() is not None

    def dbClose(self):
        self.db.close()

    def insertMany(self, urls):
        data_to_insert = [(url,) for url in urls]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO urls (url) VALUES (?)", data_to_insert
        )
        self.db.commit()
