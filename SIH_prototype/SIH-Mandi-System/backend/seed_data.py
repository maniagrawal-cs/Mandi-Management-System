"""
seed_data.py
-------------
Fills the database with sample/demo data so we can immediately
demonstrate the application without manually creating records.

Run this once, after the database has been created:
    python seed_data.py

It is safe to run again — it clears old demo rows first so you don't
end up with duplicates.
"""

from database import get_connection, init_db


def seed():
    init_db()  # make sure tables exist first
    conn = get_connection()
    cursor = conn.cursor()

    print("Clearing old demo data...")
    # Order matters because of foreign keys: children before parents.
    cursor.execute("DELETE FROM payments")
    cursor.execute("DELETE FROM queue")
    cursor.execute("DELETE FROM gate_passes")
    cursor.execute("DELETE FROM storage")
    cursor.execute("DELETE FROM farmers")
    cursor.execute("DELETE FROM officers")

    print("Adding demo farmers...")
    farmers = [
        # farmer_id, name,          mobile,       father_name,     village,  district,   state
        ("FARM1001", "Rahul Kumar",  "9876543210", "Ramesh Kumar",  "Rampur", "Karnal",   "Haryana"),
        ("FARM1002", "Amit Sharma",  "9876543211", "Suresh Sharma", "Sonipat","Sonipat",  "Haryana"),
        ("FARM1003", "Suresh Kumar", "9876543212", "Mohan Lal",     "Panipat","Panipat",  "Haryana"),
        ("FARM1004", "Mohan Singh",  "9876543213", "Gurdev Singh",  "Karnal", "Karnal",   "Haryana"),
        ("FARM1005", "Ramesh Kumar", "9876543214", "Hari Ram",      "Kaithal","Kaithal",  "Haryana"),
    ]
    cursor.executemany(
        """
        INSERT INTO farmers (farmer_id, name, mobile, father_name, village, district, state)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        farmers,
    )

    print("Adding demo officer...")
    # NOTE: plain-text password is only OK for this hackathon prototype.
    # A production system must hash passwords (e.g. with bcrypt).
    cursor.execute(
        """
        INSERT INTO officers (name, username, mobile, password)
        VALUES (?, ?, ?, ?)
        """,
        ("Officer Priya Verma", "officer1", "9998887770", "officer123"),
    )

    print("Adding demo storage capacity...")
    storage_rows = [
        ("2026-09-15", 1000, 300),
        ("2026-09-16", 1000, 0),
        ("2026-09-17", 1000, 950),  # almost full, good for demoing the "storage full" error
    ]
    cursor.executemany(
        "INSERT INTO storage (date, total_capacity, reserved_capacity) VALUES (?, ?, ?)",
        storage_rows,
    )

    conn.commit()
    conn.close()
    print("Demo data added successfully!")
    print("")
    print("You can now log in as:")
    print("  Farmer -> Name: Rahul Kumar | Mobile: 9876543210")
    print("  Officer -> Username: officer1 | Password: officer123")


if __name__ == "__main__":
    seed()
