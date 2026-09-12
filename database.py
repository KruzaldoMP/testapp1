import os
import sqlite3

DB_FILENAME = "tvs_unit_finance.db"


def get_db_path():
    """
    On Android/desktop-via-Kivy, store the DB in the app's private,
    writable data directory (App.user_data_dir). Falls back to the
    current working directory when running outside a Kivy App context
    (e.g. quick scripts/tests).
    """
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None:
            os.makedirs(app.user_data_dir, exist_ok=True)
            return os.path.join(app.user_data_dir, DB_FILENAME)
    except Exception:
        pass
    return DB_FILENAME


def get_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tvs_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                driver_name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('Income', 'Expense')),
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT
            )
        """)


def add_log_db(date, driver_name, trans_type, category, amount, description):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO tvs_logs (date, driver_name, type, category, amount, description) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date, driver_name, trans_type, category, amount, description)
        )


def update_log_db(log_id, date, driver_name, trans_type, category, amount, description):
    with get_connection() as conn:
        conn.execute(
            "UPDATE tvs_logs SET date=?, driver_name=?, type=?, category=?, amount=?, description=? "
            "WHERE id=?",
            (date, driver_name, trans_type, category, amount, description, log_id)
        )


def delete_log_db(log_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM tvs_logs WHERE id=?", (log_id,))


def get_filtered_logs_db(driver_name=None, category=None, start_date=None, end_date=None):
    query = "SELECT * FROM tvs_logs"
    conditions = []
    params = []

    if driver_name and driver_name.strip():
        conditions.append("driver_name LIKE ?")
        params.append(f"%{driver_name.strip()}%")
    if category and category != "All":
        conditions.append("category = ?")
        params.append(category)
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY date DESC, id DESC"

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def get_summary_reports_db(driver_name=None, start_date=None, end_date=None):
    conditions = []
    params = []

    if driver_name and driver_name.strip():
        conditions.append("driver_name LIKE ?")
        params.append(f"%{driver_name.strip()}%")
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_connection() as conn:
        inc_q = (f"SELECT SUM(amount) AS total FROM tvs_logs{where_clause} AND type = 'Income'"
                 if where_clause else "SELECT SUM(amount) AS total FROM tvs_logs WHERE type = 'Income'")
        exp_q = (f"SELECT SUM(amount) AS total FROM tvs_logs{where_clause} AND type = 'Expense'"
                 if where_clause else "SELECT SUM(amount) AS total FROM tvs_logs WHERE type = 'Expense'")

        income = conn.execute(inc_q, params).fetchone()["total"] or 0.0
        expense = conn.execute(exp_q, params).fetchone()["total"] or 0.0

    return income, expense
