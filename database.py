import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

DEFAULT_PROMPT = """Sen o'qituvchi yordamchisisisan. O'quvchining uy ishini tekshirib, 0 dan 100 gacha ball ber.

Vazifa: {task}

O'quvchi javobi: {homework}

Quyidagi formatda JSON qaytargin (faqat JSON, boshqa hech narsa yozma):
{{
  "score": 85,
  "feedback": "Umumiy baho va izoh (2-3 jumla)",
  "strengths": "Yaxshi bajargan joylari (ro'yxat)",
  "weaknesses": "Kamchiliklar va tavsiyalar (ro'yxat)"
}}

Mezonlar:
- To'liqlik: Vazifa to'liq bajarilganmi?
- To'g'rilik: Javob to'g'rimi?
- Tushunish: O'quvchi mavzuni tushunganmi?
- Ijodiylik: O'z fikri bormi?
"""

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        with self.get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    username TEXT,
                    registered_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    created_by INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                );
                
                CREATE TABLE IF NOT EXISTS results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    task_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    homework_text TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    feedback TEXT,
                    strengths TEXT,
                    weaknesses TEXT,
                    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    total_score INTEGER DEFAULT 0,
                    submissions INTEGER DEFAULT 0,
                    avg_score REAL DEFAULT 0,
                    UNIQUE(group_id, user_id)
                );
                
                CREATE TABLE IF NOT EXISTS group_settings (
                    group_id INTEGER PRIMARY KEY,
                    custom_prompt TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def register_user(self, user_id: int, name: str, username: Optional[str]):
        with self.get_conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (user_id, name, username) VALUES (?, ?, ?)",
                (user_id, name, username)
            )
    
    def set_task(self, group_id: int, text: str, created_by: int):
        with self.get_conn() as conn:
            # Eski vazifalarni o'chirish
            conn.execute(
                "UPDATE tasks SET is_active = 0 WHERE group_id = ?",
                (group_id,)
            )
            conn.execute(
                "INSERT INTO tasks (group_id, text, created_by) VALUES (?, ?, ?)",
                (group_id, text, created_by)
            )
    
    def get_current_task(self, group_id: int) -> Optional[Dict]:
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE group_id = ? AND is_active = 1 ORDER BY id DESC LIMIT 1",
                (group_id,)
            ).fetchone()
            return dict(row) if row else None
    
    def clear_task(self, group_id: int):
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE tasks SET is_active = 0 WHERE group_id = ?",
                (group_id,)
            )
    
    def save_result(self, group_id: int, task_id: int, user_id: int,
                    homework_text: str, score: int, feedback: str,
                    strengths: str, weaknesses: str):
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO results 
                   (group_id, task_id, user_id, homework_text, score, feedback, strengths, weaknesses)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (group_id, task_id, user_id, homework_text, score, feedback, strengths, weaknesses)
            )
    
    def update_rating(self, group_id: int, user_id: int, score: int):
        with self.get_conn() as conn:
            existing = conn.execute(
                "SELECT * FROM ratings WHERE group_id = ? AND user_id = ?",
                (group_id, user_id)
            ).fetchone()
            
            if existing:
                new_total = existing['total_score'] + score
                new_subs = existing['submissions'] + 1
                new_avg = new_total / new_subs
                conn.execute(
                    """UPDATE ratings 
                       SET total_score = ?, submissions = ?, avg_score = ?
                       WHERE group_id = ? AND user_id = ?""",
                    (new_total, new_subs, new_avg, group_id, user_id)
                )
            else:
                conn.execute(
                    """INSERT INTO ratings (group_id, user_id, total_score, submissions, avg_score)
                       VALUES (?, ?, ?, 1, ?)""",
                    (group_id, user_id, score, score)
                )
    
    def get_rating(self, group_id: int) -> List[Dict]:
        with self.get_conn() as conn:
            rows = conn.execute(
                """SELECT r.*, u.name, u.username
                   FROM ratings r
                   JOIN users u ON r.user_id = u.user_id
                   WHERE r.group_id = ?
                   ORDER BY r.avg_score DESC""",
                (group_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def get_all_results(self, group_id: int) -> List[Dict]:
        with self.get_conn() as conn:
            rows = conn.execute(
                """SELECT res.*, u.name
                   FROM results res
                   JOIN users u ON res.user_id = u.user_id
                   WHERE res.group_id = ?
                   ORDER BY res.score DESC""",
                (group_id,)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def get_user_results(self, group_id: int, user_id: int) -> List[Dict]:
        with self.get_conn() as conn:
            rows = conn.execute(
                """SELECT * FROM results
                   WHERE group_id = ? AND user_id = ?
                   ORDER BY submitted_at DESC""",
                (group_id, user_id)
            ).fetchall()
            return [dict(row) for row in rows]
    
    def set_prompt(self, group_id: int, prompt: str):
        with self.get_conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO group_settings (group_id, custom_prompt, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (group_id, prompt)
            )
    
    def get_prompt(self, group_id: int) -> str:
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT custom_prompt FROM group_settings WHERE group_id = ?",
                (group_id,)
            ).fetchone()
            return row['custom_prompt'] if row and row['custom_prompt'] else DEFAULT_PROMPT