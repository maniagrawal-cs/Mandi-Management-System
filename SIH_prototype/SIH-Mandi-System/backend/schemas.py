"""
schemas.py
-----------
This file defines the "shapes" of the data that our API expects to
receive (requests) and what it will send back (responses).

We use Pydantic models because FastAPI uses them to automatically:
- Validate incoming data
- Show nice documentation at /docs
- Give clear error messages when something is missing/wrong
"""

from pydantic import BaseModel
from typing import Optional


# ---------------------------------------------------------
# FARMER AUTH
# ---------------------------------------------------------

class FarmerLoginRequest(BaseModel):
    name: str
    mobile: str


# ---------------------------------------------------------
# OFFICER AUTH
# ---------------------------------------------------------

class OfficerLoginRequest(BaseModel):
    username: str
    password: str


# ---------------------------------------------------------
# GATE PASS
# ---------------------------------------------------------

class GatePassCreateRequest(BaseModel):
    farmer_id: str
    crop_type: str
    crop_name: str
    mandi: str
    vehicle_number: str
    vehicle_type: str
    desired_date: str          # format: YYYY-MM-DD
    estimated_weight: float    # in quintals


# ---------------------------------------------------------
# QR SCAN
# ---------------------------------------------------------

class ScanRequest(BaseModel):
    gate_pass_id: str


# ---------------------------------------------------------
# STAGE UPDATE
# ---------------------------------------------------------

class StageUpdateRequest(BaseModel):
    gate_pass_id: str
    new_stage: str


# ---------------------------------------------------------
# PAYMENT
# ---------------------------------------------------------

class PaymentRequest(BaseModel):
    gate_pass_id: str
    amount: float
