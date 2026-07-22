import sqlite3, json, os, threading
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "memory.db")

class Memory:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.local = threading.local()
        self._init_db()

    def _conn(self):
        if not hasattr(self.local, 'conn') or self.local.conn is None:
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn

    def _init_db(self):
        c = self._conn()
        c.executescript("""
        CREATE TABLE IF NOT EXISTS short_term (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS long_term (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            namespace TEXT,
            key TEXT,
            value TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(namespace, key)
        );
        CREATE TABLE IF NOT EXISTS episodic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            agent_id TEXT,
            agent_name TEXT,
            action TEXT,
            input_summary TEXT,
            output_summary TEXT,
            status TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS semantic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            predicate TEXT,
            object TEXT,
            confidence REAL DEFAULT 1.0,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS agent_state (
            agent_id TEXT PRIMARY KEY,
            state TEXT,
            context TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS workflow_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            workflow_id TEXT,
            status TEXT,
            current_node TEXT,
            dag_definition TEXT,
            result TEXT,
            created_at TEXT,
            updated_at TEXT
        );
        """)
        c.commit()

    def clear_short_term(self):
        self._conn().execute("DELETE FROM short_term")
        self._conn().commit()

    def set_short(self, key, value):
        now = datetime.utcnow().isoformat()
        val = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        self._conn().execute(
            "INSERT OR REPLACE INTO short_term (key, value, updated_at) VALUES (?, ?, ?)",
            (key, val, now)
        )
        self._conn().commit()

    def get_short(self, key, default=None):
        row = self._conn().execute("SELECT value FROM short_term WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        val = row["value"]
        try: return json.loads(val)
        except: return val

    def get_all_short(self):
        rows = self._conn().execute("SELECT key, value FROM short_term").fetchall()
        result = {}
        for r in rows:
            try: result[r["key"]] = json.loads(r["value"])
            except: result[r["key"]] = r["value"]
        return result

    def store_long(self, namespace, key, value):
        now = datetime.utcnow().isoformat()
        val = json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value
        self._conn().execute(
            "INSERT OR REPLACE INTO long_term (namespace, key, value, created_at, updated_at) "
            "VALUES (?, ?, ?, COALESCE((SELECT created_at FROM long_term WHERE namespace=? AND key=?), ?), ?)",
            (namespace, key, val, namespace, key, now, now)
        )
        self._conn().commit()

    def get_long(self, namespace, key, default=None):
        row = self._conn().execute(
            "SELECT value FROM long_term WHERE namespace=? AND key=?", (namespace, key)
        ).fetchone()
        if row is None:
            return default
        val = row["value"]
        try: return json.loads(val)
        except: return val

    def search_long(self, namespace, query):
        rows = self._conn().execute(
            "SELECT key, value FROM long_term WHERE namespace=? AND (key LIKE ? OR value LIKE ?)",
            (namespace, f"%{query}%", f"%{query}%")
        ).fetchall()
        result = {}
        for r in rows:
            try: result[r["key"]] = json.loads(r["value"])
            except: result[r["key"]] = r["value"]
        return result

    def record_episode(self, session_id, agent_id, agent_name, action, input_summary, output_summary, status):
        now = datetime.utcnow().isoformat()
        self._conn().execute(
            "INSERT INTO episodic (session_id, agent_id, agent_name, action, input_summary, output_summary, status, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (session_id, agent_id, agent_name, action,
             json.dumps(input_summary, ensure_ascii=False)[:500],
             json.dumps(output_summary, ensure_ascii=False)[:500],
             status, now)
        )
        self._conn().commit()

    def get_history(self, agent_id=None, limit=20):
        if agent_id:
            rows = self._conn().execute(
                "SELECT * FROM episodic WHERE agent_id=? ORDER BY id DESC LIMIT ?",
                (agent_id, limit)
            ).fetchall()
        else:
            rows = self._conn().execute(
                "SELECT * FROM episodic ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def add_relation(self, subject, predicate, obj, confidence=1.0):
        now = datetime.utcnow().isoformat()
        self._conn().execute(
            "INSERT INTO semantic (subject, predicate, object, confidence, created_at) VALUES (?, ?, ?, ?, ?)",
            (subject, predicate, obj, confidence, now)
        )
        self._conn().commit()

    def query_relations(self, subject=None, predicate=None, obj=None):
        sql = "SELECT * FROM semantic WHERE 1=1"
        params = []
        if subject: sql += " AND subject=?"; params.append(subject)
        if predicate: sql += " AND predicate=?"; params.append(predicate)
        if obj: sql += " AND object=?"; params.append(obj)
        rows = self._conn().execute(sql + " ORDER BY confidence DESC", params).fetchall()
        return [dict(r) for r in rows]

    def save_agent_state(self, agent_id, state, context=None):
        now = datetime.utcnow().isoformat()
        ctx = json.dumps(context, ensure_ascii=False) if context else "{}"
        self._conn().execute(
            "INSERT OR REPLACE INTO agent_state (agent_id, state, context, updated_at) VALUES (?, ?, ?, ?)",
            (agent_id, json.dumps(state, ensure_ascii=False), ctx, now)
        )
        self._conn().commit()

    def get_agent_state(self, agent_id):
        row = self._conn().execute(
            "SELECT state, context FROM agent_state WHERE agent_id=?", (agent_id,)
        ).fetchone()
        if row is None: return {"state": "idle", "context": {}}
        return {
            "state": json.loads(row["state"]),
            "context": json.loads(row["context"])
        }

    def save_workflow(self, session_id, workflow_id, status, current_node, dag_def, result=None):
        now = datetime.utcnow().isoformat()
        existing = self._conn().execute(
            "SELECT id FROM workflow_state WHERE session_id=? AND workflow_id=?",
            (session_id, workflow_id)
        ).fetchone()
        if existing:
            self._conn().execute(
                "UPDATE workflow_state SET status=?, current_node=?, result=?, updated_at=? WHERE session_id=? AND workflow_id=?",
                (status, current_node, json.dumps(result, ensure_ascii=False) if result else None, now, session_id, workflow_id)
            )
        else:
            self._conn().execute(
                "INSERT INTO workflow_state (session_id, workflow_id, status, current_node, dag_definition, result, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, workflow_id, status, current_node,
                 json.dumps(dag_def, ensure_ascii=False),
                 json.dumps(result, ensure_ascii=False) if result else None,
                 now, now)
            )
        self._conn().commit()

    def get_workflow(self, session_id, workflow_id):
        row = self._conn().execute(
            "SELECT * FROM workflow_state WHERE session_id=? AND workflow_id=?",
            (session_id, workflow_id)
        ).fetchone()
        if row is None: return None
        d = dict(row)
        for field in ["dag_definition", "result"]:
            if d.get(field) and isinstance(d[field], str):
                try: d[field] = json.loads(d[field])
                except: pass
        return d

    def close(self):
        if hasattr(self.local, 'conn') and self.local.conn:
            self.local.conn.close()
            self.local.conn = None
