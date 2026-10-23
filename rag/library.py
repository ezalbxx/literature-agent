"""Persistent, collection-scoped BM25 retrieval. No network or model calls."""
from collections import Counter
from contextlib import contextmanager
from pathlib import Path
import hashlib
import math
import re
import sqlite3
import uuid


def tokens(text):
    """英文按词、中文按相邻两字切分；这是词法检索，不是语义编码。"""
    text = text.casefold()
    words = re.findall(r'[a-z0-9_]+', text)
    for span in re.findall(r'[\u4e00-\u9fff]+', text):
        words.extend(span[i:i+2] for i in range(max(1, len(span)-1)))
    return words


def split_page(text, size=1200, overlap=160):
    """只在单页内部切块，返回原页字符偏移，避免引用页码被切块破坏。"""
    text = text.replace('\x00', '').strip()
    if not 0 <= overlap < size:
        raise ValueError('Invalid chunk overlap')
    for start in range(0, len(text), size-overlap):
        yield start, text[start:start+size]
        if start+size >= len(text):
            break


class Library:
    """一个数据库可保存多个文献库；所有读取都显式限制 collection。"""
    def __init__(self, database):
        self.path = Path(database)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS collections (id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS documents (
                    collection TEXT, id TEXT, title TEXT, kind TEXT, url TEXT,
                    PRIMARY KEY(collection,id));
                CREATE TABLE IF NOT EXISTS chunks (
                    collection TEXT, id TEXT, document TEXT, page INTEGER,
                    offset INTEGER, text TEXT, PRIMARY KEY(collection,id));
                CREATE INDEX IF NOT EXISTS chunks_collection ON chunks(collection);
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self):
        identifier = uuid.uuid4().hex
        with self.connect() as db:
            db.execute('INSERT INTO collections VALUES (?)', (identifier,))
        return identifier

    def require(self, collection):
        if not re.fullmatch('[0-9a-f]{32}', collection):
            raise ValueError('Invalid collection id')
        with self.connect() as db:
            if not db.execute('SELECT 1 FROM collections WHERE id=?', (collection,)).fetchone():
                raise KeyError('Collection not found')

    def add_pages(self, collection, title, pages, kind='pdf', url=''):
        """事务性入库。相同页文字重复导入时保留原记录，不追加副本。"""
        self.require(collection)
        if not pages or len(pages) > 100 or sum(len(p) for p in pages) > 1_000_000:
            raise ValueError('Document must contain 1–100 pages and at most 1M characters')
        if not any(p.strip() for p in pages):
            raise ValueError('No extractable text; scanned PDFs need OCR before import')
        # Content, rather than a filename or local path, defines identity.
        identity = hashlib.sha256('\f'.join(pages).encode()).hexdigest()[:24]
        rows = []
        for page, text in enumerate(pages, 1):
            for offset, chunk in split_page(text):
                chunk_id = f'{identity}-p{page}-o{offset}'
                rows.append((collection, chunk_id, identity, page, offset, chunk))
        with self.connect() as db:
            if db.execute('SELECT 1 FROM documents WHERE collection=? AND id=?',
                          (collection, identity)).fetchone():
                return {'id': identity, 'chunks': len(rows), 'duplicate': True}
            if db.execute('SELECT COUNT(*) FROM chunks WHERE collection=?',
                          (collection,)).fetchone()[0] + len(rows) > 3000:
                raise ValueError('Collection limit of 3000 chunks reached')
            db.execute('INSERT INTO documents VALUES (?,?,?,?,?)',
                       (collection, identity, title[:300], kind, url))
            db.executemany('INSERT INTO chunks VALUES (?,?,?,?,?,?)', rows)
        return {'id': identity, 'chunks': len(rows), 'duplicate': False}

    def add_pdf(self, collection, filename, payload):
        if len(payload) > 20*1024*1024 or not payload.startswith(b'%PDF-'):
            raise ValueError('A PDF of at most 20 MiB is required')
        import pymupdf
        try:
            with pymupdf.open(stream=payload, filetype='pdf') as doc:
                if doc.is_encrypted or not 1 <= len(doc) <= 100:
                    raise ValueError('Encrypted or over-100-page PDF')
                pages = [page.get_text() for page in doc]
        except Exception:
            raise ValueError('PDF cannot be read; provide an unencrypted PDF with text') from None
        return self.add_pages(collection, filename, pages)

    def documents(self, collection):
        self.require(collection)
        with self.connect() as db:
            return [dict(r) for r in db.execute(
                'SELECT id,title,kind,url FROM documents WHERE collection=? ORDER BY rowid',
                (collection,))]

    def chunks(self, collection):
        self.require(collection)
        with self.connect() as db:
            return [dict(r) for r in db.execute('''
                SELECT c.id,c.document,c.page,c.offset,c.text,d.title,d.url,d.kind
                FROM chunks c JOIN documents d
                ON c.collection=d.collection AND c.document=d.id
                WHERE c.collection=? ORDER BY c.id''', (collection,))]

    def search(self, collection, query, limit=5):
        """BM25 = IDF × 饱和词频 / 长度惩罚；不命中的片段不强行返回。"""
        if not query.strip() or len(query) > 2000 or type(limit) is not int or not 1 <= limit <= 10:
            raise ValueError('Invalid search query or limit')
        chunks = self.chunks(collection)
        if not chunks:
            return []
        counts = [Counter(tokens(c['text'])) for c in chunks]
        lengths = [sum(c.values()) for c in counts]
        average = sum(lengths)/len(chunks) or 1
        dfs = Counter(t for c in counts for t in c)
        scored = []
        for chunk, count, length in zip(chunks, counts, lengths):
            score = 0.0
            for token in set(tokens(query)):
                frequency = count[token]
                if frequency:
                    idf = math.log(1+(len(chunks)-dfs[token]+0.5)/(dfs[token]+0.5))
                    score += idf*frequency*2.5/(frequency+1.5*(0.25+0.75*length/average))
            if score > 0:
                scored.append(dict(chunk, score=round(score, 6)))
        return sorted(scored, key=lambda c: (-c['score'], c['id']))[:limit]

    def page(self, collection, document, page):
        if type(page) is not int or page < 1:
            raise ValueError('Invalid page')
        # Bound model context even when a page contains unusually much text.
        return [c for c in self.chunks(collection)
                if c['document'] == document and c['page'] == page][:5]
