from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
import uuid

STATES = ('new', 'investigating', 'resolved', 'dismissed')
DISPOSITIONS = ('unreviewed', 'suspicious', 'benign', 'confirmed')

def now():
    return datetime.now(timezone.utc).isoformat()

@contextmanager
def connection(path, readonly=False):
    con = sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro', uri=True, timeout=30) if readonly else sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    try:
        yield con
        if not readonly:
            con.commit()
    finally:
        con.close()

class Store:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / 'jobs').mkdir(parents=True, exist_ok=True)
        self.catalog = self.root / 'catalog.sqlite'
        with connection(self.catalog) as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,status TEXT,phase TEXT,created_at TEXT,updated_at TEXT,error TEXT,parameters TEXT,summary TEXT)')

    def folder(self, job_id):
        # Never derive paths from an unchecked request ID.
        if self.job(job_id) is None:
            raise KeyError(job_id)
        return self.root / 'jobs' / job_id

    def create_job(self, parameters, job_id=None):
        job_id = job_id or uuid.uuid4().hex
        if not job_id.replace('-', '').isalnum() or len(job_id) > 64:
            raise ValueError('Invalid job ID')
        with connection(self.catalog) as con:
            con.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?)', (job_id, 'queued', 'waiting', now(), now(), None, json.dumps(parameters), '{}'))
        (self.root / 'jobs' / job_id).mkdir()
        return self.job(job_id)

    def update_job(self, job_id, status, phase, summary=None, error=None):
        with connection(self.catalog) as con:
            con.execute('UPDATE jobs SET status=?,phase=?,summary=?,error=?,updated_at=? WHERE id=?', (status, phase, json.dumps(summary or {}), error, now(), job_id))

    def job(self, job_id):
        with connection(self.catalog, True) as con:
            row = con.execute('SELECT * FROM jobs WHERE id=?', (job_id,)).fetchone()
        if row is None:
            return None
        result = dict(row)
        result['parameters'] = json.loads(result['parameters']); result['summary'] = json.loads(result['summary'])
        return result

    def jobs(self):
        with connection(self.catalog, True) as con:
            ids = [r[0] for r in con.execute('SELECT id FROM jobs ORDER BY created_at DESC')]
        return [self.job(i) for i in ids]

    def recover(self):
        with connection(self.catalog) as con:
            con.execute("UPDATE jobs SET status='failed',phase='interrupted',error='Server restarted before processing completed; upload again.',updated_at=? WHERE status IN ('queued','running')", (now(),))

    def index_groups(self, job_id, groups):
        with connection(self.folder(job_id) / 'index.sqlite') as con:
            con.execute('PRAGMA journal_mode=WAL')
            con.executescript('''CREATE TABLE incidents(id TEXT PRIMARY KEY,scenario TEXT,priority REAL,band TEXT,status TEXT DEFAULT 'new',disposition TEXT DEFAULT 'unreviewed',note TEXT DEFAULT '',payload TEXT,search_text TEXT);
              CREATE INDEX incident_rank ON incidents(priority DESC,id);
              CREATE TABLE feedback(id INTEGER PRIMARY KEY,incident_id TEXT,status TEXT,disposition TEXT,note TEXT,created_at TEXT);''')
            con.executemany('INSERT INTO incidents(id,scenario,priority,band,payload,search_text) VALUES (?,?,?,?,?,?)', [(g['id'], g['scenario'], g['priority'], g['priority_band'], json.dumps(g), ' '.join([g['title'], *g['signature_counts'], *g['hosts'], *g['destinations'], *g['anchor']]).lower()) for g in groups])

    def incident(self, job_id, incident_id):
        with connection(self.folder(job_id) / 'index.sqlite', True) as con:
            row = con.execute('SELECT * FROM incidents WHERE id=?', (incident_id,)).fetchone()
        if row is None:
            return None
        result = json.loads(row['payload'])
        result['review'] = dict(status=row['status'], disposition=row['disposition'], note=row['note'])
        return result

    def all_groups(self, job_id):
        with connection(self.folder(job_id) / 'index.sqlite', True) as con:
            return [json.loads(r[0]) for r in con.execute('SELECT payload FROM incidents ORDER BY priority DESC,id')]

    def list_incidents(self, job_id, limit, offset, scenario=None, band=None, status=None, search=None, min_priority=0, include_dismissed=False):
        clauses = ['priority>=?']; values = [min_priority]
        for col, value in [('scenario', scenario), ('band', band), ('status', status)]:
            if value:
                clauses.append(f'{col}=?'); values.append(value)
        if not include_dismissed and status != 'dismissed':
            clauses.append("status!='dismissed'")
        if search:
            clauses.append("search_text LIKE ? ESCAPE '\\'")
            values.append('%' + search.lower().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%')
        where = ' AND '.join(clauses)
        with connection(self.folder(job_id) / 'index.sqlite', True) as con:
            count = con.execute(f'SELECT count(*) FROM incidents WHERE {where}', values).fetchone()[0]
            rows = con.execute(f'SELECT payload,status,disposition,note FROM incidents WHERE {where} ORDER BY priority DESC,id LIMIT ? OFFSET ?', values + [limit, offset]).fetchall()
        items = []
        for r in rows:
            g = json.loads(r['payload']); g.pop('evidence', None)
            g['review'] = dict(status=r['status'], disposition=r['disposition'], note=r['note'])
            items.append(g)
        return dict(items=items, total=count, limit=limit, offset=offset)

    def evidence(self, job_id, incident_id, limit=50, offset=0):
        with connection(self.folder(job_id) / 'evidence.sqlite', True) as con:
            count = con.execute('SELECT count(*) FROM alerts WHERE group_id=?', (incident_id,)).fetchone()[0]
            rows = con.execute('SELECT id,normalized,raw FROM alerts WHERE group_id=? ORDER BY time,id LIMIT ? OFFSET ?', (incident_id, limit, offset)).fetchall()
        return dict(total=count, limit=limit, offset=offset, items=[dict(alert_id=r['id'], normalized=json.loads(r['normalized']), original_record=json.loads(r['raw'])) for r in rows])

    def evidence_ids(self, job_id, incident_id, ids):
        if not ids:
            return []
        marks = ','.join('?' for _ in ids)
        with connection(self.folder(job_id) / 'evidence.sqlite', True) as con:
            rows = con.execute(f'SELECT id,normalized,raw FROM alerts WHERE group_id=? AND id IN ({marks}) ORDER BY time,id', [incident_id, *ids]).fetchall()
        return [dict(alert_id=r['id'], normalized=json.loads(r['normalized']), original_record=json.loads(r['raw'])) for r in rows]

    def feedback(self, job_id, incident_id, status, disposition, note):
        with connection(self.folder(job_id) / 'index.sqlite') as con:
            con.execute('UPDATE incidents SET status=?,disposition=?,note=? WHERE id=?', (status, disposition, note, incident_id))
            con.execute('INSERT INTO feedback(incident_id,status,disposition,note,created_at) VALUES (?,?,?,?,?)', (incident_id, status, disposition, note, now()))
        return self.incident(job_id, incident_id)

    def stats(self, job_id):
        with connection(self.folder(job_id) / 'index.sqlite', True) as con:
            rows = [dict(r) for r in con.execute('SELECT scenario,band,status,disposition,count(*) incidents FROM incidents GROUP BY scenario,band,status,disposition')]
        return dict(job=self.job(job_id), breakdown=rows, total_incidents=sum(r['incidents'] for r in rows))
