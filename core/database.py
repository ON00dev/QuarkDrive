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


# Adicionar estes metodos à classe MetadataDB:

def get_total_files(self):
    """Obter numero total de arquivos"""
    cur = self.conn.cursor()
    cur.execute('SELECT COUNT(*) FROM files')
    return cur.fetchone()[0]

def get_total_blobs(self):
    """Obter numero total de blobs unicos"""
    cur = self.conn.cursor()
    cur.execute('SELECT COUNT(*) FROM blobs')
    return cur.fetchone()[0]

def get_total_original_size(self):
    """Obter tamanho total original de todos os blobs"""
    cur = self.conn.cursor()
    cur.execute('SELECT SUM(size_original * ref_count) FROM blobs')
    result = cur.fetchone()[0]
    return result if result else 0

def get_total_compressed_size(self):
    """Obter tamanho total comprimido de todos os blobs"""
    cur = self.conn.cursor()
    cur.execute('SELECT SUM(size_compressed) FROM blobs')
    result = cur.fetchone()[0]
    return result if result else 0

def get_duplicate_files_count(self):
    """Obter numero de arquivos duplicados"""
    cur = self.conn.cursor()
    cur.execute('''
        SELECT COUNT(*) FROM files f
        JOIN blobs b ON f.hash = b.hash
        WHERE b.ref_count > 1
    ''')
    return cur.fetchone()[0]

def get_compression_stats(self):
    """Obter estatisticas detalhadas de compressao"""
    cur = self.conn.cursor()
    cur.execute('''
        SELECT 
            SUM(size_original * ref_count) as total_original,
            SUM(size_compressed) as total_compressed,
            AVG((size_original - size_compressed) * 100.0 / size_original) as avg_compression_ratio,
            COUNT(*) as total_blobs
        FROM blobs
        WHERE size_original > 0
    ''')
    return cur.fetchone()

def get_storage_efficiency(self):
    """Calcular eficiência de armazenamento"""
    cur = self.conn.cursor()
    cur.execute('''
        SELECT 
            COUNT(DISTINCT f.hash) as unique_files,
            COUNT(f.id) as total_files,
            SUM(f.size) as total_file_size,
            SUM(b.size_compressed) as total_storage_used
        FROM files f
        JOIN blobs b ON f.hash = b.hash
    ''')
    return cur.fetchone()
