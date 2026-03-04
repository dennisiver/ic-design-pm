"""SQLite 資料庫管理：Schema 建立與 CRUD 操作"""

import sqlite3
import os
from pathlib import Path
from models import Project, Task
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
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id    INTEGER NOT NULL,
    title         TEXT    NOT NULL,
    description   TEXT    DEFAULT '',
    status        TEXT    NOT NULL DEFAULT '待辦',
    priority      TEXT    NOT NULL DEFAULT '中',
    category      TEXT    DEFAULT '',
    assignee      TEXT    DEFAULT '',
    due_date      TEXT    DEFAULT NULL,
    sort_order    INTEGER DEFAULT 0,
    created_at    TEXT    DEFAULT (datetime('now','localtime')),
    updated_at    TEXT    DEFAULT (datetime('now','localtime')),
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

CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_assignee       ON tasks(assignee);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date       ON tasks(due_date);

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
        self._seed_default_project()

    def _seed_default_project(self):
        count = self.conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if count == 0:
            self.conn.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                ("預設專案", "預設的專案空間")
            )
            self.conn.commit()

    def close(self):
        self.conn.close()

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
            (name, description, color)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_project(self, project_id, name, description='', color='#4A90D9'):
        self.conn.execute(
            "UPDATE projects SET name=?, description=?, color=? WHERE id=?",
            (name, description, color, project_id)
        )
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
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        query += (" ORDER BY CASE priority "
                   "WHEN '緊急' THEN 0 WHEN '高' THEN 1 "
                   "WHEN '中' THEN 2 WHEN '低' THEN 3 END, "
                   "created_at DESC")
        rows = self.conn.execute(query, params).fetchall()
        return [Task(**{k: dict(r)[k] for k in dict(r) if k != 'tags'}) for r in rows]

    def get_task_by_id(self, task_id):
        row = self.conn.execute(
            "SELECT * FROM tasks WHERE id=?", (task_id,)
        ).fetchone()
        if not row:
            return None
        task = Task(**{k: dict(row)[k] for k in dict(row) if k != 'tags'})
        # 載入標籤
        tag_rows = self.conn.execute(
            "SELECT t.name FROM tags t JOIN task_tags tt ON t.id=tt.tag_id "
            "WHERE tt.task_id=?", (task_id,)
        ).fetchall()
        task.tags = [r['name'] for r in tag_rows]
        return task

    def create_task(self, project_id, title, description='', status='待辦',
                    priority='中', category='', assignee='', due_date=None, tags=None):
        cur = self.conn.execute(
            "INSERT INTO tasks (project_id, title, description, status, "
            "priority, category, assignee, due_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (project_id, title, description, status, priority,
             category, assignee, due_date)
        )
        task_id = cur.lastrowid
        if tags:
            self._set_task_tags(task_id, tags)
        self.conn.commit()
        return task_id

    def update_task(self, task_id, title, description='', status='待辦',
                    priority='中', category='', assignee='', due_date=None, tags=None):
        self.conn.execute(
            "UPDATE tasks SET title=?, description=?, status=?, priority=?, "
            "category=?, assignee=?, due_date=? WHERE id=?",
            (title, description, status, priority, category, assignee,
             due_date, task_id)
        )
        if tags is not None:
            self._set_task_tags(task_id, tags)
        self.conn.commit()

    def update_task_status(self, task_id, new_status):
        self.conn.execute(
            "UPDATE tasks SET status=? WHERE id=?",
            (new_status, task_id)
        )
        self.conn.commit()

    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    def get_unique_assignees(self):
        rows = self.conn.execute(
            "SELECT DISTINCT assignee FROM tasks WHERE assignee != '' ORDER BY assignee"
        ).fetchall()
        return [r['assignee'] for r in rows]

    # ─── Tags ────────────────────────────────────────────────

    def _set_task_tags(self, task_id, tag_names):
        self.conn.execute("DELETE FROM task_tags WHERE task_id=?", (task_id,))
        for name in tag_names:
            name = name.strip()
            if not name:
                continue
            row = self.conn.execute(
                "SELECT id FROM tags WHERE name=?", (name,)
            ).fetchone()
            if row:
                tag_id = row['id']
            else:
                cur = self.conn.execute(
                    "INSERT INTO tags (name) VALUES (?)", (name,)
                )
                tag_id = cur.lastrowid
            self.conn.execute(
                "INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)",
                (task_id, tag_id)
            )
