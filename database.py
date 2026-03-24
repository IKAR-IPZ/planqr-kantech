import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str = "kantech_events.db"):
        base_dir = Path(__file__).resolve().parent
        self.db_path = str((base_dir / db_path).resolve()) if not Path(db_path).is_absolute() else db_path
        self._last_seen_access: Dict[str, datetime] = {}
        self._last_seen_count: Dict[str, int] = {}
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tblDydaktyk (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    card_hex TEXT NOT NULL,
                    opened_at DATETIME NOT NULL,
                    closed_at DATETIME,
                    status TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tblUser (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    card_hex TEXT NOT NULL,
                    last_access DATETIME NOT NULL,
                    status TEXT,
                    dydaktyk_id INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_dydaktyk_active
                ON tblDydaktyk(is_active)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_dydaktyk_username
                ON tblDydaktyk(username)
            ''')

            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_dydaktyk_username_unique
                ON tblDydaktyk(username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_username
                ON tblUser(username)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_card_hex
                ON tblUser(card_hex)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_dydaktyk_id
                ON tblUser(dydaktyk_id)
            ''')
            
            cursor.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_user_unique
                ON tblUser(username, card_hex)
            ''')
            
            conn.commit()
            print(f"Database initialized: {self.db_path}")
    
    def _is_dydaktyk(self, username: str) -> bool:
        return username.strip().lower().startswith("g")

    def _is_close_status(self, status: str) -> bool:
        status_l = status.strip().lower()
        return "close" in status_l or "closed" in status_l or "zamkn" in status_l

    def get_active_dydaktyk_id(self) -> Optional[int]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM tblDydaktyk
                    WHERE is_active = 1
                    ORDER BY opened_at DESC
                    LIMIT 1
                ''')
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"Error getting active dydaktyk: {e}")
            return None

    def get_active_dydaktyk(self) -> Optional[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM tblDydaktyk
                    WHERE is_active = 1
                    ORDER BY opened_at DESC
                    LIMIT 1
                ''')
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Error getting active dydaktyk details: {e}")
            return None

    def open_dydaktyk(self, username: str, card_hex: str, opened_at: datetime, status: str) -> Optional[int]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tblDydaktyk
                    SET is_active = 0, closed_at = ?, updated_at = ?
                    WHERE is_active = 1
                ''', (opened_at, datetime.now()))

                cursor.execute('SELECT id FROM tblDydaktyk WHERE username = ?', (username,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute('''
                        UPDATE tblDydaktyk
                        SET card_hex = ?, opened_at = ?, closed_at = NULL, status = ?, is_active = 1, updated_at = ?
                        WHERE username = ?
                    ''', (card_hex, opened_at, status, datetime.now(), username))
                    conn.commit()
                    return existing[0]

                cursor.execute('''
                    INSERT INTO tblDydaktyk
                    (username, card_hex, opened_at, status, is_active)
                    VALUES (?, ?, ?, ?, 1)
                ''', (username, card_hex, opened_at, status))

                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Error opening dydaktyk: {e}")
            return None

    def close_active_dydaktyk(self, closed_at: datetime, status: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tblDydaktyk
                    SET closed_at = ?, status = ?, is_active = 0, updated_at = ?
                    WHERE is_active = 1
                ''', (closed_at, status, datetime.now()))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error closing dydaktyk: {e}")
            return False

    def save_user_with_relation(self, username: str, card_hex: str, last_access: datetime,
                                status: str, dydaktyk_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id FROM tblUser
                    WHERE username = ? AND card_hex = ?
                ''', (username, card_hex))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute('''
                        UPDATE tblUser
                        SET dydaktyk_id = ?, updated_at = ?
                        WHERE username = ? AND card_hex = ?
                    ''', (dydaktyk_id, datetime.now(), username, card_hex))
                else:
                    cursor.execute('''
                        INSERT INTO tblUser
                        (username, card_hex, last_access, status, dydaktyk_id)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (username, card_hex, last_access, status, dydaktyk_id))

                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving user with relation: {e}")
            return False

    def get_user_relation(self, username: str, card_hex: str) -> Optional[int]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT dydaktyk_id FROM tblUser
                    WHERE username = ? AND card_hex = ?
                    LIMIT 1
                ''', (username, card_hex))
                row = cursor.fetchone()
                return row[0] if row and row[0] is not None else None
        except Exception as e:
            print(f"Error getting user relation: {e}")
            return None

    def get_latest_user_access(self, limit: int = 10) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM tblUser
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving user access events: {e}")
            return []

    def get_latest_dydaktyk(self, limit: int = 10) -> List[Dict]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM tblDydaktyk
                    ORDER BY opened_at DESC
                    LIMIT ?
                ''', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error retrieving dydaktyk events: {e}")
            return []

    def close(self):
        """Close database connection"""
        pass
    
    def parse_and_save_access_data(self, raw_data: str) -> List[Dict]:
        """Parse access data table format and save to database"""
        saved_records = []
        try:
            lines = raw_data.strip().split('\n')
            data_lines = [line for line in lines if line.strip() and '---' not in line and 'User' not in line]
            
            for line in data_lines:
                parts = line.split()
                if len(parts) >= 5:
                    try:
                        username = parts[0]
                        try:
                            count = int(parts[1])
                        except ValueError:
                            count = None
                        card_hex = parts[2]
                        date_str = ' '.join(parts[3:5])
                        status = ' '.join(parts[5:])
                        last_access = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

                        if self._is_dydaktyk(username):
                            key = f"{username}|{card_hex}"
                            
                            # Check if this dydaktyk already has active session
                            cursor = sqlite3.connect(self.db_path).cursor()
                            cursor.execute('SELECT id FROM tblDydaktyk WHERE username = ? AND is_active = 1', (username,))
                            existing_active = cursor.fetchone()
                            cursor.close()
                            
                            if existing_active:
                                # Second swipe - close the active session
                                if self.close_active_dydaktyk(last_access, "Second swipe"):
                                    saved_records.append({
                                        'type': 'dydaktyk_close',
                                        'username': username,
                                        'card_hex': card_hex,
                                        'status': 'Second swipe'
                                    })
                                    print(f"Closed dydaktyk (second swipe): {username}")
                                continue
                            
                            if self._is_close_status(status):
                                if self.close_active_dydaktyk(last_access, status):
                                    saved_records.append({
                                        'type': 'dydaktyk_close',
                                        'username': username,
                                        'card_hex': card_hex,
                                        'status': status
                                    })
                                    print(f"Closed dydaktyk: {username} - {status}")
                            else:
                                dydaktyk_id = self.open_dydaktyk(username, card_hex, last_access, status)
                                if dydaktyk_id:
                                    saved_records.append({
                                        'type': 'dydaktyk_open',
                                        'username': username,
                                        'card_hex': card_hex,
                                        'dydaktyk_id': dydaktyk_id,
                                        'status': status
                                    })
                                    print(f"Opened dydaktyk: {username} - {card_hex} - id {dydaktyk_id}")
                        else:
                            active = self.get_active_dydaktyk()
                            dydaktyk_id = active.get("id") if active else None
                            active_opened_at = None
                            if active:
                                try:
                                    active_opened_at = datetime.fromisoformat(active.get("opened_at"))
                                except Exception:
                                    active_opened_at = None
                            if dydaktyk_id:
                                if active_opened_at and last_access < active_opened_at:
                                    continue
                                key = f"{username}|{card_hex}"
                                last_seen = self._last_seen_access.get(key)
                                last_seen_count = self._last_seen_count.get(key)
                                existing_relation = self.get_user_relation(username, card_hex)
                                if last_seen and last_access <= last_seen and existing_relation == dydaktyk_id:
                                    if count is None or last_seen_count is None or count <= last_seen_count:
                                        continue
                                if self.save_user_with_relation(username, card_hex, last_access, status, dydaktyk_id):
                                    if not last_seen or last_access > last_seen:
                                        self._last_seen_access[key] = last_access
                                    if count is not None:
                                        self._last_seen_count[key] = count
                                    saved_records.append({
                                        'type': 'user',
                                        'username': username,
                                        'card_hex': card_hex,
                                        'dydaktyk_id': dydaktyk_id,
                                        'status': status
                                    })
                                    print(f"Saved user: {username} - {card_hex} -> dydaktyk {dydaktyk_id}")
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing line: {line} - {e}")
                        continue
        except Exception as e:
            print(f"Error parsing access data: {e}")
        
        return saved_records
