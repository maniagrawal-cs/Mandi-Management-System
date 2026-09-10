"""
crud.py
--------
This file contains all the functions that actually talk to the
database (Create, Read, Update, Delete = "CRUD").

Keeping all database logic in one place makes main.py (our API
routes) much shorter and easier to read.
"""

from datetime import datetime, date as date_cls
from database import get_connection


# The exact order the queue stages happen in. We use this list to
# figure out what the "next" stage is when a QR is scanned or when
# an officer clicks "Move to Next Stage".
STAGE_ORDER = [
    "GATE_PASS_GENERATED",
    "ARRIVED",
    "QUALITY",
    "WEIGHT",
    "STORAGE",
    "PAYMENT",
    "COMPLETED",
]


# =====================================================================
# FARMERS
# =====================================================================

def get_farmer_by_name_mobile(name: str, mobile: str):
    """
    Looks up a farmer using their name + mobile number.
    Matching is case-insensitive and ignores extra spaces, since
    farmers may type their name slightly differently.
    """
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM farmers
        WHERE LOWER(TRIM(name)) = LOWER(TRIM(?)) AND mobile = ?
        """,
        (name, mobile),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_farmer_by_id(farmer_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM farmers WHERE farmer_id = ?", (farmer_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# =====================================================================
# OFFICERS
# =====================================================================

def get_officer_by_username(username: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM officers WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# =====================================================================
# STORAGE CAPACITY
# =====================================================================

DEFAULT_TOTAL_CAPACITY = 1000  # quintals, used if a date has no record yet


def get_storage(date: str):
    """
    Returns the storage record for a date. If no record exists yet,
    we create one automatically using a default total capacity, so
    the demo works even for dates the officer never pre-configured.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM storage WHERE date = ?", (date,)).fetchone()

    if row is None:
        conn.execute(
            "INSERT INTO storage (date, total_capacity, reserved_capacity) VALUES (?, ?, 0)",
            (date, DEFAULT_TOTAL_CAPACITY),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM storage WHERE date = ?", (date,)).fetchone()

    conn.close()
    return dict(row)


def reserve_storage(date: str, weight: float):
    """
    Adds `weight` quintals to the reserved capacity for a date.
    Caller must already have checked there is enough room available.
    """
    conn = get_connection()
    conn.execute(
        "UPDATE storage SET reserved_capacity = reserved_capacity + ? WHERE date = ?",
        (weight, date),
    )
    conn.commit()
    conn.close()


def has_enough_storage(date: str, requested_weight: float):
    """
    Checks whether `requested_weight` quintals can still fit into
    the given date's storage capacity.

    Returns a tuple: (is_available: bool, available_quintals: float)
    """
    storage = get_storage(date)
    available = storage["total_capacity"] - storage["reserved_capacity"]
    return requested_weight <= available, available


# =====================================================================
# GATE PASSES
# =====================================================================

def generate_gate_pass_id():
    """
    Creates a unique, human-readable Gate Pass ID such as:
        GP-2026-0001

    The number increases for every gate pass created in the current
    year. This keeps IDs short and easy to read on a printed pass.
    """
    year = datetime.now().year
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM gate_passes WHERE gate_pass_id LIKE ?",
        (f"GP-{year}-%",),
    ).fetchone()["c"]
    conn.close()

    next_number = count + 1
    return f"GP-{year}-{next_number:04d}"


def farmer_has_active_pass_for_date(farmer_id: str, desired_date: str):
    """Prevents a farmer from generating two gate passes for the same date."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT * FROM gate_passes
        WHERE farmer_id = ? AND desired_date = ? AND status = 'ACTIVE'
        """,
        (farmer_id, desired_date),
    ).fetchone()
    conn.close()
    return row is not None


def create_gate_pass(farmer_id, crop_type, crop_name, mandi, vehicle_number,
                      vehicle_type, desired_date, estimated_weight):
    """
    Creates a new gate pass, reserves storage, and adds the farmer
    to the queue for their chosen date. Returns the new gate_pass_id.
    """
    gate_pass_id = generate_gate_pass_id()
    created_at = datetime.now().isoformat(timespec="seconds")

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO gate_passes
            (gate_pass_id, farmer_id, crop_type, crop_name, mandi,
             vehicle_number, vehicle_type, desired_date, estimated_weight,
             status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        """,
        (gate_pass_id, farmer_id, crop_type, crop_name, mandi,
         vehicle_number, vehicle_type, desired_date, estimated_weight,
         created_at),
    )

    # Work out the next queue position for that date.
    next_position = conn.execute(
        "SELECT COUNT(*) as c FROM queue WHERE queue_date = ?", (desired_date,)
    ).fetchone()["c"] + 1

    conn.execute(
        """
        INSERT INTO queue (gate_pass_id, farmer_id, queue_date, position, stage)
        VALUES (?, ?, ?, ?, 'GATE_PASS_GENERATED')
        """,
        (gate_pass_id, farmer_id, desired_date, next_position),
    )

    conn.commit()
    conn.close()

    # Reserve the storage capacity (separate helper, its own connection).
    reserve_storage(desired_date, estimated_weight)

    return gate_pass_id


def get_gate_pass(gate_pass_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM gate_passes WHERE gate_pass_id = ?", (gate_pass_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_gate_passes_for_farmer(farmer_id: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM gate_passes WHERE farmer_id = ? ORDER BY created_at DESC",
        (farmer_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =====================================================================
# QUEUE
# =====================================================================

def get_queue_entry(gate_pass_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM queue WHERE gate_pass_id = ?", (gate_pass_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_queue_by_date(queue_date: str):
    """Returns every queue entry for a date, ordered by position, joined with farmer name."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT queue.*, farmers.name as farmer_name, gate_passes.crop_name
        FROM queue
        JOIN farmers ON queue.farmer_id = farmers.farmer_id
        JOIN gate_passes ON queue.gate_pass_id = gate_passes.gate_pass_id
        WHERE queue.queue_date = ?
        ORDER BY queue.position ASC
        """,
        (queue_date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_queue_summary_for_farmer(gate_pass_id: str):
    """
    Builds the "Live Queue" view for a farmer: their stage, how many
    farmers are ahead of them (not yet completed), and how many are
    still waiting overall.
    """
    entry = get_queue_entry(gate_pass_id)
    if entry is None:
        return None

    all_entries = get_queue_by_date(entry["queue_date"])

    stage_index = STAGE_ORDER.index(entry["stage"])

    # "Ahead" = farmers scheduled the same day who are further along
    # in the process (later stage) than this farmer, and not finished.
    farmers_ahead = 0
    farmers_waiting = 0
    for e in all_entries:
        if e["gate_pass_id"] == gate_pass_id:
            continue
        other_index = STAGE_ORDER.index(e["stage"])
        if e["stage"] == "GATE_PASS_GENERATED":
            farmers_waiting += 1
        if other_index > stage_index and e["stage"] != "COMPLETED":
            farmers_ahead += 1

    return {
        "gate_pass_id": gate_pass_id,
        "stage": entry["stage"],
        "position": entry["position"],
        "farmers_ahead": farmers_ahead,
        "farmers_waiting": farmers_waiting,
        "total_in_queue": len(all_entries),
    }


def move_to_next_stage(gate_pass_id: str, target_stage: str = None):
    """
    Moves a gate pass forward in the queue.

    - If target_stage is given, jump straight to that stage (used by
      the officer dashboard buttons).
    - Otherwise, just advance one step forward (used by QR scanning).

    Returns the new stage, or raises ValueError if the move isn't valid.
    """
    entry = get_queue_entry(gate_pass_id)
    if entry is None:
        raise ValueError("Gate pass not found in queue.")

    current_index = STAGE_ORDER.index(entry["stage"])

    if target_stage:
        if target_stage not in STAGE_ORDER:
            raise ValueError("Unknown stage name.")
        new_index = STAGE_ORDER.index(target_stage)
        if new_index != current_index + 1:
            raise ValueError("You can only move to the next stage in order.")
    else:
        if current_index == len(STAGE_ORDER) - 1:
            raise ValueError("This gate pass has already completed the process.")
        new_index = current_index + 1

    new_stage = STAGE_ORDER[new_index]

    conn = get_connection()
    conn.execute(
        "UPDATE queue SET stage = ? WHERE gate_pass_id = ?",
        (new_stage, gate_pass_id),
    )
    conn.commit()
    conn.close()

    return new_stage


# =====================================================================
# PAYMENTS
# =====================================================================

def generate_transaction_id():
    return "TXN" + datetime.now().strftime("%Y%m%d%H%M%S")


def create_payment(gate_pass_id: str, farmer_id: str, amount: float):
    transaction_id = generate_transaction_id()
    payment_date = date_cls.today().isoformat()

    conn = get_connection()
    conn.execute(
        """
        INSERT INTO payments (gate_pass_id, farmer_id, amount, transaction_id, payment_date, status)
        VALUES (?, ?, ?, ?, ?, 'COMPLETED')
        """,
        (gate_pass_id, farmer_id, amount, transaction_id, payment_date),
    )
    conn.commit()
    conn.close()

    return {
        "gate_pass_id": gate_pass_id,
        "farmer_id": farmer_id,
        "amount": amount,
        "transaction_id": transaction_id,
        "payment_date": payment_date,
        "status": "COMPLETED",
    }


def get_payment_history(farmer_id: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM payments WHERE farmer_id = ? ORDER BY payment_date DESC",
        (farmer_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_payment_for_gate_pass(gate_pass_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM payments WHERE gate_pass_id = ? ORDER BY payment_date DESC LIMIT 1",
        (gate_pass_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
