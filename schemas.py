from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# ── Shared Enums ───────────────────────────────────────────────────────────────

class UserRole(str, Enum):
    donor    = "donor"
    hospital = "hospital"

class UrgencyLevel(str, Enum):
    normal    = "normal"
    urgent    = "urgent"
    emergency = "emergency"

class RequestStatus(str, Enum):
    open      = "open"
    fulfilled = "fulfilled"


# ── User Schemas ───────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name:     str        = Field(..., min_length=2, max_length=100)
    email:    EmailStr
    password: str        = Field(..., min_length=6)
    role:     UserRole   = UserRole.donor

class UserResponse(BaseModel):
    id:         int
    name:       str
    email:      str
    role:       UserRole
    created_at: datetime

    class Config:
        from_attributes = True


# ── Auth Schemas ───────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email:    str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


# ── Donor Schemas ──────────────────────────────────────────────────────────────

class DonorCreate(BaseModel):
    user_id:      int
    blood_type:   str  = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    city:         str  = Field(..., min_length=2, max_length=100)
    phone:        str  = Field(..., min_length=7, max_length=20)
    is_available: bool = True
    last_donated: Optional[datetime] = None

class DonorResponse(BaseModel):
    id:           int
    user_id:      int
    blood_type:   str
    city:         str
    phone:        str
    is_available: bool
    last_donated: Optional[datetime]

    class Config:
        from_attributes = True

class DonorUpdate(BaseModel):
    is_available: bool


# ── Blood Request Schemas ──────────────────────────────────────────────────────

class BloodRequestCreate(BaseModel):
    hospital_name: str          = Field(..., min_length=2, max_length=150)
    blood_type:    str          = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    city:          str          = Field(..., min_length=2, max_length=100)
    units_needed:  int          = Field(..., ge=1)
    urgency:       UrgencyLevel = UrgencyLevel.normal

class BloodRequestResponse(BaseModel):
    id:            int
    hospital_name: str
    blood_type:    str
    city:          str
    units_needed:  int
    urgency:       UrgencyLevel
    status:        RequestStatus
    created_at:    datetime

    class Config:
        from_attributes = True


# ── Inventory Schemas ──────────────────────────────────────────────────────────

class InventoryCreate(BaseModel):
    hospital_name:   str = Field(..., min_length=2, max_length=150)
    city:            str = Field(..., min_length=2, max_length=100)
    blood_type:      str = Field(..., pattern=r"^(A|B|AB|O)[+-]$")
    units_available: int = Field(..., ge=0)

class InventoryResponse(BaseModel):
    id:              int
    hospital_name:   str
    city:            str
    blood_type:      str
    units_available: int
    updated_at:      datetime

    class Config:
        from_attributes = True