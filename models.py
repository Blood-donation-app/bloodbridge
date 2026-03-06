from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    donor    = "donor"
    hospital = "hospital"

class UrgencyLevel(str, enum.Enum):
    normal    = "normal"
    urgent    = "urgent"
    emergency = "emergency"

class RequestStatus(str, enum.Enum):
    open      = "open"
    fulfilled = "fulfilled"


# ── Models ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(Enum(UserRole), nullable=False, default=UserRole.donor)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relationship: one user -> one donor profile
    donor = relationship("Donor", back_populates="user", uselist=False)


class Donor(Base):
    __tablename__ = "donors"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    blood_type    = Column(String(5), nullable=False)          # e.g. A+, O-, AB+
    city          = Column(String(100), nullable=False)
    phone         = Column(String(20), nullable=False)
    is_available  = Column(Boolean, default=True)
    last_donated  = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="donor")


class BloodRequest(Base):
    __tablename__ = "blood_requests"

    id            = Column(Integer, primary_key=True, index=True)
    hospital_name = Column(String(150), nullable=False)
    blood_type    = Column(String(5), nullable=False)
    city          = Column(String(100), nullable=False)
    units_needed  = Column(Integer, nullable=False)
    urgency       = Column(Enum(UrgencyLevel), default=UrgencyLevel.normal, nullable=False)
    status        = Column(Enum(RequestStatus), default=RequestStatus.open, nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class Inventory(Base):
    __tablename__ = "inventory"

    id              = Column(Integer, primary_key=True, index=True)
    hospital_name   = Column(String(150), nullable=False)
    city            = Column(String(100), nullable=False)
    blood_type      = Column(String(5), nullable=False)
    units_available = Column(Integer, nullable=False, default=0)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)