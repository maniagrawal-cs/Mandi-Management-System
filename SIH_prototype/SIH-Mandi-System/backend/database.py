"""
database.py
------------
This file handles everything related to connecting to our SQLite database
and creating the tables we need.

We are using plain SQLite3 (no heavy ORM) because this is a simple
hackathon prototype and we want the code to stay easy to read.
"""

import sqlite3
import os

# The database file will be created in the same folder as this script.
DB_FILE = os.path.join(os.path.dirname(__file__), "mandi.db")


def get_connection():
    """
    Creates and returns a new connection to the SQLite database.

    We set row_factory to sqlite3.Row so that we can access columns
    by name (like a dictionary) instead of only by index number.
    This makes the rest of our code much easier to read.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints (off by default in SQLite).
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """
    Creates all the tables used by the application, if they don't
    already exist. This is safe to run every time the app starts.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ------------------------------------------------------------
    # FARMERS TABLE
    # In a real system, this data would already exist because it
    # comes from a government farmer database. For our prototype,
    # we simulate that by pre-loading farmers using seed_data.py.
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            father_name TEXT,
            village TEXT,
            district TEXT,
            state TEXT
        )
    """)

    # ------------------------------------------------------------
    # OFFICERS TABLE
    # Officers already exist in the system and only log in
    # (they do not self-register).
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS officers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            mobile TEXT,
            password TEXT NOT NULL
        )
    """)

    # ------------------------------------------------------------
    # GATE PASSES TABLE
    # One row is created every time a farmer generates a gate pass.
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gate_passes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate_pass_id TEXT UNIQUE NOT NULL,
            farmer_id TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            crop_name TEXT NOT NULL,
            mandi TEXT NOT NULL,
            vehicle_number TEXT NOT NULL,
            vehicle_type TEXT NOT NULL,
            desired_date TEXT NOT NULL,
            estimated_weight REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'ACTIVE',
            created_at TEXT NOT NULL,
            FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id)
        )
    """)

    # ------------------------------------------------------------
    # QUEUE TABLE
    # Tracks which stage each gate pass / farmer is currently at,
    # grouped by the date they are scheduled to arrive.
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate_pass_id TEXT UNIQUE NOT NULL,
            farmer_id TEXT NOT NULL,
            queue_date TEXT NOT NULL,
            position INTEGER NOT NULL,
            stage TEXT NOT NULL DEFAULT 'GATE_PASS_GENERATED',
            FOREIGN KEY (gate_pass_id) REFERENCES gate_passes (gate_pass_id),
            FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id)
        )
    """)

    # ------------------------------------------------------------
    # PAYMENTS TABLE
    # Stores simulated payments made to farmers after procurement.
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gate_pass_id TEXT NOT NULL,
            farmer_id TEXT NOT NULL,
            amount REAL NOT NULL,
            transaction_id TEXT UNIQUE NOT NULL,
            payment_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'COMPLETED',
            FOREIGN KEY (gate_pass_id) REFERENCES gate_passes (gate_pass_id),
            FOREIGN KEY (farmer_id) REFERENCES farmers (farmer_id)
        )
    """)

    # ------------------------------------------------------------
    # STORAGE TABLE
    # Tracks total and reserved storage capacity (in quintals) for
    # every procurement date.
    # ------------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS storage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            total_capacity REAL NOT NULL,
            reserved_capacity REAL NOT NULL DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized. Tables are ready.")


if __name__ == "__main__":
    # Running "python database.py" directly will just set up the tables.
    init_db()
