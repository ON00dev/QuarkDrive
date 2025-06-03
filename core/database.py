import sqlite3
import os

class MetadataDB:
    def __init__(self, db_path='metadata.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_tables()

    def create_tables(self):
        cur = self.conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                hash TEXT,
                size INTEGER
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS blobs (
                hash TEXT PRIMARY KEY,
                compressed_path TEXT,
                size_original INTEGER,
                size_compressed INTEGER,
                ref_count INTEGER DEFAULT 1
            )
        ''')

        self.conn.commit()

    def add_file(self, path, hash_value, size):
        cur = self.conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO files (path, hash, size)
            VALUES (?, ?, ?)
        ''', (path, hash_value, size))
        self.conn.commit()

    def get_file_by_path(self, path):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM files WHERE path=?', (path,))
        return cur.fetchone()

    def add_blob(self, hash_value, compressed_path, size_original, size_compressed):
        cur = self.conn.cursor()
        cur.execute('''
            INSERT OR IGNORE INTO blobs (hash, compressed_path, size_original, size_compressed, ref_count)
            VALUES (?, ?, ?, ?, 1)
        ''', (hash_value, compressed_path, size_original, size_compressed))
        self.conn.commit()

    def increment_blob_ref(self, hash_value):
        cur = self.conn.cursor()
        cur.execute('''
            UPDATE blobs SET ref_count = ref_count + 1 WHERE hash=?
        ''', (hash_value,))
        self.conn.commit()

    def decrement_blob_ref(self, hash_value):
        cur = self.conn.cursor()
        cur.execute('''
            UPDATE blobs SET ref_count = ref_count - 1 WHERE hash=?
        ''', (hash_value,))
        self.conn.commit()

    def get_blob(self, hash_value):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM blobs WHERE hash=?', (hash_value,))
        return cur.fetchone()

    def close(self):
        self.conn.close()
