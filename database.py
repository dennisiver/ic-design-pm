"""SQLite 資料庫管理：Schema 建立與 CRUD 操作"""

import sqlite3
import os
from pathlib import Path
from models import Project, Task, WorkLog, Milestone
from constants import DB_FOLDER_NAME, DB_FILE_NAME

SCHEMA_SQL = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS projects (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    description   TEXT    DEFAULT '',
    color         TEXT    DEFAULT '#4A90D9',
    sort_order    INTEGER DEFAULT 0,
    is_archived   INTEGER DEFAULT 0,
    created_at    TEXT    DEFAULT (datetime('now','localtime')),
    updated_at    TEXT    DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL,
    title           TEXT    NOT NULL,
    description     TEXT    DEFAULT '',
    status          TEXT    NOT NULL DEFAULT '待辦',
    priority        TEXT    NOT NULL DEFAULT '中',
    category        TEXT    DEFAULT '',
    assignee        TEXT    DEFAULT '',
    due_date        TEXT    DEFAULT NULL,
    start_date      TEXT    DEFAULT NULL,
    estimated_weeks INTEGER DEFAULT NULL,
    sort_order      INTEGER DEFAULT 0,
    created_at      TEXT    DEFAULT (datetime('now','localtime')),
    updated_at      TEXT    DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tags (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL UNIQUE,
    color         TEXT    DEFAULT '#6C757D'
);

CREATE TABLE IF NOT EXISTS task_tags (
    task_id       INTEGER NOT NULL,
    tag_id        INTEGER NOT NULL,
    PRIMARY KEY (task_id, tag_id),
    FOREIGN KEY (task_id)  REFERENCES tasks(id)  ON DELETE CASCADE,
    FOREIGN KEY (tag_id)   REFERENCES tags(id)   ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS work_logs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     INTEGER NOT NULL,
    log_date    TEXT    NOT NULL,
    content     TEXT    DEFAULT '',
    hours       REAL    DEFAULT 0.0,
    created_at  TEXT    DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS milestones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL,
    name        TEXT    NOT NULL,
    target_date TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    created_at  TEXT    DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);

CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee       ON tasks(assignee);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date       ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_work_logs_task        ON work_logs(task_id);
CREATE INDEX IF NOT EXISTS idx_work_logs_date        ON work_logs(log_date);
CREATE INDEX IF NOT EXISTS idx_milestones_project    ON milestones(project_id);

CREATE TRIGGER IF NOT EXISTS trg_tasks_updated_at
AFTER UPDATE ON tasks
BEGIN
    UPDATE tasks SET updated_at = datetime('now','localtime') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_projects_updated_at
AFTER UPDATE ON projects
BEGIN
    UPDATE projects SET updated_at = datetime('now','localtime') WHERE id = NEW.id;
END;
"""

# 用於從 sqlite3.Row 建立 Task 時排除不存在的欄位
TASK_FIELDS = {f.name for f in Task.__dataclass_fields__.values() if f.name != 'tags'}


class DatabaseManager:
    def __init__(self, db_path=None):
        if db_path is None:
            app_dir = Path(os.environ.get('APPDATA', '.')) / DB_FOLDER_NAME
            app_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(app_dir / DB_FILE_NAME)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.conn.execute("PRAGMA journal_mode=WAL")

    def initialize(self):
        self.conn.executescript(SCHEMA_SQL)
        self._migrate()
        self._seed_default_project()

    # ─── 資料庫遷移 ─────────────────────────────────────────

    def _migrate(self):
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)")
        row = self.conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        current = row[0] if row[0] is not None else 0

        migrations = [
            self._migrate_v1_to_v2,
            self._migrate_v2_add_milestone_sort,
        ]
        for i, fn in enumerate(migrations, start=1):
            if current < i:
                fn()
                self.conn.execute(
                    "INSERT OR REPLACE INTO schema_version (version) VALUES (?)", (i,))
                self.conn.commit()

    def _migrate_v1_to_v2(self):
        for col in ['start_date TEXT DEFAULT NULL',
                     'estimated_weeks INTEGER DEFAULT NULL']:
            try:
                self.conn.execute(f"ALTER TABLE tasks ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass

    def _migrate_v2_add_milestone_sort(self):
        try:
            self.conn.execute(
                "ALTER TABLE milestones ADD COLUMN sort_order INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    def _seed_default_project(self):
        count = self.conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if count == 0:
            self.conn.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                ("預設專案", "預設的專案空間"))
            self.conn.commit()

    def close(self):
        self.conn.close()

    def _row_to_task(self, row):
        d = dict(row)
        return Task(**{k: d[k] for k in d if k in TASK_FIELDS})

    # ─── Projects ────────────────────────────────────────────

    def get_all_projects(self):
        rows = self.conn.execute(
            "SELECT * FROM projects WHERE is_archived=0 ORDER BY sort_order, name"
        ).fetchall()
        return [Project(**dict(r)) for r in rows]

    def get_project_by_id(self, project_id):
        row = self.conn.execute(
            "SELECT * FROM projects WHERE id=?", (project_id,)
        ).fetchone()
        return Project(**dict(row)) if row else None

    def create_project(self, name, description='', color='#4A90D9'):
        cur = self.conn.execute(
            "INSERT INTO projects (name, description, color) VALUES (?, ?, ?)",
            (name, description, color))
        self.conn.commit()
        return cur.lastrowid

    def update_project(self, project_id, name, description='', color='#4A90D9'):
        self.conn.execute(
            "UPDATE projects SET name=?, description=?, color=? WHERE id=?",
            (name, description, color, project_id))
        self.conn.commit()

    def delete_project(self, project_id):
        self.conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        self.conn.commit()

    # ─── Tasks ───────────────────────────────────────────────

    def get_tasks(self, project_id=None, status=None, category=None,
                  priority=None, assignee=None, search=None):
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if project_id is not None:
            query += " AND project_id=?"
            params.append(project_id)
        if status:
            query += " AND status=?"
            params.append(status)
        if category:
            query += " AND category=?"
            params.append(category)
        if priority:
            query += " AND priority=?"
            params.append(priority)
        if assignee:
            query += " AND assignee=?"
            params.append(assignee)
        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR assignee LIKE ?)"
            params.extend([f'%{search}%'] * 3)
        query += (" ORDER BY CASE priority "
                   "WHEN '緊急' THEN 0 WHEN '高' THEN 1 "
                   "WHEN '中' THEN 2 WHEN '低' THEN 3 END, "
                   "created_at DESC")
        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def get_task_by_id(self, task_id):
        row = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if not row:
            return None
        task = self._row_to_task(row)
        tag_rows = self.conn.execute(
            "SELECT t.name FROM tags t JOIN task_tags tt ON t.id=tt.tag_id "
            "WHERE tt.task_id=?", (task_id,)).fetchall()
        task.tags = [r['name'] for r in tag_rows]
        return task

    def create_task(self, project_id, title, description='', status='待辦',
                    priority='中', category='', assignee='', due_date=None,
                    start_date=None, estimated_weeks=None, tags=None):
        cur = self.conn.execute(
            "INSERT INTO tasks (project_id, title, description, status, "
            "priority, category, assignee, due_date, start_date, estimated_weeks) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, title, description, status, priority,
             category, assignee, due_date, start_date, estimated_weeks))
        task_id = cur.lastrowid
        if tags:
            self._set_task_tags(task_id, tags)
        self.conn.commit()
        return task_id

    def update_task(self, task_id, title, description='', status='待辦',
                    priority='中', category='', assignee='', due_date=None,
                    start_date=None, estimated_weeks=None, tags=None):
        self.conn.execute(
            "UPDATE tasks SET title=?, description=?, status=?, priority=?, "
            "category=?, assignee=?, due_date=?, start_date=?, estimated_weeks=? "
            "WHERE id=?",
            (title, description, status, priority, category, assignee,
             due_date, start_date, estimated_weeks, task_id))
        if tags is not None:
            self._set_task_tags(task_id, tags)
        self.conn.commit()

    def update_task_status(self, task_id, new_status):
        self.conn.execute(
            "UPDATE tasks SET status=? WHERE id=?", (new_status, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def get_unique_assignees(self):
        rows = self.conn.execute(
            "SELECT DISTINCT assignee FROM tasks WHERE assignee != '' ORDER BY assignee"
        ).fetchall()
        return [r['assignee'] for r in rows]

    def get_unique_categories(self):
        rows = self.conn.execute(
            "SELECT DISTINCT category FROM tasks WHERE category != '' ORDER BY category"
        ).fetchall()
        return [r['category'] for r in rows]

    def get_task_tags_bulk(self):
        """回傳 {task_id: [tag_name, ...]} 對照表"""
        rows = self.conn.execute(
            "SELECT tt.task_id, t.name FROM task_tags tt "
            "JOIN tags t ON t.id=tt.tag_id").fetchall()
        result = {}
        for r in rows:
            result.setdefault(r['task_id'], []).append(r['name'])
        return result

    # ─── Tags ────────────────────────────────────────────────

    def _set_task_tags(self, task_id, tag_names):
        self.conn.execute("DELETE FROM task_tags WHERE task_id=?", (task_id,))
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            row = self.conn.execute(
                "SELECT id FROM tags WHERE name=?", (name,)).fetchone()
            if row:
                tag_id = row['id']
            else:
                cur = self.conn.execute(
                    "INSERT INTO tags (name) VALUES (?)", (name,))
                tag_id = cur.lastrowid
            self.conn.execute(
                "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                (task_id, tag_id))

    # ─── Work Logs ───────────────────────────────────────────

    def get_work_logs(self, task_id):
        rows = self.conn.execute(
            "SELECT * FROM work_logs WHERE task_id=? "
            "ORDER BY log_date DESC, created_at DESC", (task_id,)).fetchall()
        return [WorkLog(**dict(r)) for r in rows]

    def create_work_log(self, task_id, log_date, content='', hours=0.0):
        cur = self.conn.execute(
            "INSERT INTO work_logs (task_id, log_date, content, hours) "
            "VALUES (?, ?, ?, ?)", (task_id, log_date, content, hours))
        self.conn.commit()
        return cur.lastrowid

    def update_work_log(self, log_id, log_date, content, hours):
        self.conn.execute(
            "UPDATE work_logs SET log_date=?, content=?, hours=? WHERE id=?",
            (log_date, content, hours, log_id))
        self.conn.commit()

    def delete_work_log(self, log_id):
        self.conn.execute("DELETE FROM work_logs WHERE id=?", (log_id,))
        self.conn.commit()

    # ─── Milestones ──────────────────────────────────────────

    def get_milestones(self, project_id=None):
        if project_id:
            rows = self.conn.execute(
                "SELECT * FROM milestones WHERE project_id=? ORDER BY target_date",
                (project_id,)).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM milestones ORDER BY target_date").fetchall()
        return [Milestone(**dict(r)) for r in rows]

    def create_milestone(self, project_id, name, target_date, description=''):
        cur = self.conn.execute(
            "INSERT INTO milestones (project_id, name, target_date, description) "
            "VALUES (?, ?, ?, ?)", (project_id, name, target_date, description))
        self.conn.commit()
        return cur.lastrowid

    def update_milestone(self, mid, name, target_date, description=''):
        self.conn.execute(
            "UPDATE milestones SET name=?, target_date=?, description=? WHERE id=?",
            (name, target_date, description, mid))
        self.conn.commit()

    def delete_milestone(self, mid):
        self.conn.execute("DELETE FROM milestones WHERE id=?", (mid,))
        self.conn.commit()

    def update_gantt_order(self, task_orders, milestone_orders):
        """批次更新甘特圖排序。
        task_orders: [(task_id, sort_order), ...]
        milestone_orders: [(milestone_id, sort_order), ...]
        """
        for tid, order in task_orders:
            self.conn.execute(
                "UPDATE tasks SET sort_order=? WHERE id=?", (order, tid))
        for mid, order in milestone_orders:
            self.conn.execute(
                "UPDATE milestones SET sort_order=? WHERE id=?", (order, mid))
        self.conn.commit()

    # ─── Dashboard Stats ────────────────────────────────────

    def get_dashboard_stats(self, project_id=None):
        where = "WHERE 1=1"
        params = []
        if project_id:
            where += " AND project_id=?"
            params.append(project_id)
        stats = {}
        for key, col in [('by_status', 'status'), ('by_priority', 'priority')]:
            rows = self.conn.execute(
                f"SELECT {col}, COUNT(*) as cnt FROM tasks {where} GROUP BY {col}",
                params).fetchall()
            stats[key] = [(r[col], r['cnt']) for r in rows]
        # by assignee
        rows = self.conn.execute(
            f"SELECT COALESCE(NULLIF(assignee,''),'未指派') as a, COUNT(*) as cnt "
            f"FROM tasks {where} GROUP BY a", params).fetchall()
        stats['by_assignee'] = [(r['a'], r['cnt']) for r in rows]
        # by category
        rows = self.conn.execute(
            f"SELECT COALESCE(NULLIF(category,''),'未分類') as c, COUNT(*) as cnt "
            f"FROM tasks {where} GROUP BY c", params).fetchall()
        stats['by_category'] = [(r['c'], r['cnt']) for r in rows]
        return stats

    def get_project_progress(self):
        """回傳各專案的任務進度統計清單。
        回傳: [{name, total, done, in_progress}, ...]
        """
        rows = self.conn.execute(
            "SELECT p.id, p.name, "
            "COUNT(t.id) as total, "
            "SUM(CASE WHEN t.status='已完成' THEN 1 ELSE 0 END) as done, "
            "SUM(CASE WHEN t.status='進行中' THEN 1 ELSE 0 END) as in_progress "
            "FROM projects p "
            "LEFT JOIN tasks t ON t.project_id = p.id "
            "WHERE p.is_archived = 0 "
            "GROUP BY p.id "
            "ORDER BY p.name"
        ).fetchall()
        return [
            {
                'name': r['name'],
                'total': r['total'] or 0,
                'done': r['done'] or 0,
                'in_progress': r['in_progress'] or 0,
            }
            for r in rows
        ]
