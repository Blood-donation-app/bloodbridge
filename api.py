from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import case
from typing import Optional
from database import SessionLocal
from models import Donor
from schemas import DonorCreate, DonorUpdate, DonorResponse

router = APIRouter(prefix="/donors", tags=["Donors"])



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── 1. POST /donors — create a new donor profile ─────────────────────────────
@router.post("/", response_model=DonorResponse, status_code=201)
def create_donor(donor: DonorCreate, db: Session = Depends(get_db)):
    """Create a new donor profile."""
    db_donor = Donor(
        user_id=donor.user_id,
        blood_type=donor.blood_type,
        city=donor.city,
        phone=donor.phone,
        last_donated=donor.last_donated,
        is_available=True,  # default to available on creation
    )
    db.add(db_donor)
    db.commit()
    db.refresh(db_donor)
    return db_donor


# ── 2. GET /donors — list all donors with optional filters ───────────────────
@router.get("/", response_model=list[DonorResponse])
def get_donors(
    blood_type: Optional[str] = Query(None, description="Filter by blood type, e.g. O+"),
    city: Optional[str] = Query(None, description="Filter by city, e.g. Solapur"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    db: Session = Depends(get_db),
):
    """
    Return all donors with optional filters.
    Results are sorted so available donors appear first.
    Example: /donors?blood_type=O%2B&city=Solapur
    """
    query = db.query(Donor)

    if blood_type:
        query = query.filter(Donor.blood_type == blood_type)
    if city:
        query = query.filter(Donor.city.ilike(city))  # case-insensitive match
    if is_available is not None:
        query = query.filter(Donor.is_available == is_available)

    # Sort: available donors (True) first, then unavailable (False)
    query = query.order_by(
        case((Donor.is_available == True, 0), else_=1)
    )

    return query.all()


# ── 3. PATCH /donors/{donor_id}/availability — toggle availability ────────────
@router.patch("/{donor_id}/availability", response_model=DonorResponse)
def update_donor_availability(
    donor_id: int,
    payload: DonorUpdate,
    db: Session = Depends(get_db),
):
    """Toggle a donor's is_available status."""
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail=f"Donor {donor_id} not found")

    donor.is_available = payload.is_available
    db.commit()
    db.refresh(donor)
    return donor


# ── 4. GET /donors/{donor_id} — fetch a single donor's full profile ──────────
@router.get("/{donor_id}", response_model=DonorResponse)
def get_donor(donor_id: int, db: Session = Depends(get_db)):
    """Return a single donor's full profile."""
    donor = db.query(Donor).filter(Donor.id == donor_id).first()
    if not donor:
        raise HTTPException(status_code=404, detail=f"Donor {donor_id} not found")
    return donor