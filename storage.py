"""Local audit log; SHA-256 is not a tamper-proof ledger."""
import sqlite3
from pathlib import Path
from datetime import datetime,timezone
from core import fingerprint

def initialize(path):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, created_utc TEXT, scenario_id TEXT, decision TEXT, reviewer TEXT, rationale TEXT, input_hash TEXT, output_hash TEXT)')

def add_review(path, scenario_id, decision, reviewer, rationale, source, result):
    if decision not in ('approved','needs_revision','rejected'): raise ValueError('Invalid decision')
    if len(reviewer.strip()) < 2 or len(rationale.strip()) < 5: raise ValueError('Reviewer and rationale required')
    initialize(path)
    with sqlite3.connect(path) as db:
        cur=db.execute('INSERT INTO reviews (created_utc,scenario_id,decision,reviewer,rationale,input_hash,output_hash) VALUES (?,?,?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(),scenario_id,decision,reviewer.strip(),rationale.strip(),fingerprint(source),fingerprint(result)))
        return cur.lastrowid

def reviews(path):
    initialize(path)
    with sqlite3.connect(path) as db:
        db.row_factory=sqlite3.Row
        return [dict(row) for row in db.execute('SELECT * FROM reviews ORDER BY id DESC')]
