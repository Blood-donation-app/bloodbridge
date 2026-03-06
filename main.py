from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime
from api import router as donor_router
from fastapi.staticfiles import StaticFiles
import uuid

from database import engine, get_db, Base
import models
import schemas

# ── App Init ───────────────────────────────────────────────────────────────────

app = FastAPI(
    title="BloodBridge API",
    description="Connecting blood donors with hospitals in real time.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(donor_router)
app.mount("/app", StaticFiles(directory="blood-donation", html=True), name="frontend")

# ── Password Hashing ───────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── DB Setup + Seed Data ───────────────────────────────────────────────────────

def seed_data(db: Session):
    """Insert dummy donors if the DB is empty."""
    if db.query(models.User).count() > 0:
        return  # Already seeded

    seed_users = [
        {"name": "Alice Fernandes", "email": "alice@example.com", "city": "Mumbai",    "blood_type": "O+",  "phone": "9876543210"},
        {"name": "Ravi Kumar",      "email": "ravi@example.com",  "city": "Delhi",     "blood_type": "A-",  "phone": "9123456789"},
        {"name": "Priya Singh",     "email": "priya@example.com", "city": "Bangalore", "blood_type": "B+",  "phone": "9988776655"},
        {"name": "Omar Sheikh",     "email": "omar@example.com",  "city": "Hyderabad", "blood_type": "AB+", "phone": "9001122334"},
        {"name": "Sneha Patil",     "email": "sneha@example.com", "city": "Pune",      "blood_type": "O-",  "phone": "9765432109"},
    ]

    for entry in seed_users:
        user = models.User(
            name          = entry["name"],
            email         = entry["email"],
            password_hash = hash_password("password123"),
            role          = models.UserRole.donor,
        )
        db.add(user)
        db.flush()  # Get user.id before committing

        donor = models.Donor(
            user_id      = user.id,
            blood_type   = entry["blood_type"],
            city         = entry["city"],
            phone        = entry["phone"],
            is_available = True,
            last_donated = None,
        )
        db.add(donor)

    db.commit()
    print("✅ Seed data inserted: 5 donors across Mumbai, Delhi, Bangalore, Hyderabad, Pune.")


@app.on_event("startup")
def startup():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    # Seed dummy data
    db = next(get_db())
    try:
        seed_data(db)
    finally:
        db.close()


# ── Health Check ───────────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok"}


# ── Auth Endpoints ─────────────────────────────────────────────────────────────

@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user (donor or hospital)."""
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered."
        )

    user = models.User(
        name          = payload.name,
        email         = payload.email,
        password_hash = hash_password(payload.password),
        role          = payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/login", response_model=schemas.LoginResponse, tags=["Auth"])
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Authenticate a user and return a token."""
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate a placeholder token (replace with real JWT in production)
    fake_token = f"bloodbridge-token-{uuid.uuid4().hex}"

    return schemas.LoginResponse(
        access_token=fake_token,
        token_type="bearer",
        user=schemas.UserResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            created_at=user.created_at,
        ),
    )


# ── Blood Request Endpoints ────────────────────────────────────────────────────

@app.get("/blood-requests", response_model=list[schemas.BloodRequestResponse], tags=["Blood Requests"])
def list_blood_requests(
    city:       str | None = None,
    blood_type: str | None = None,
    status:     str | None = None,
    db: Session = Depends(get_db)
):
    """List all blood requests with optional filters."""
    query = db.query(models.BloodRequest)
    if city:
        query = query.filter(models.BloodRequest.city.ilike(f"%{city}%"))
    if blood_type:
        query = query.filter(models.BloodRequest.blood_type == blood_type)
    if status:
        query = query.filter(models.BloodRequest.status == status)
    return query.all()


@app.post("/blood-requests", response_model=schemas.BloodRequestResponse, status_code=status.HTTP_201_CREATED, tags=["Blood Requests"])
def create_blood_request(payload: schemas.BloodRequestCreate, db: Session = Depends(get_db)):
    """Submit a new blood request."""
    request = models.BloodRequest(**payload.model_dump())
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


# ── Inventory Endpoints ────────────────────────────────────────────────────────

@app.get("/inventory", response_model=list[schemas.InventoryResponse], tags=["Inventory"])
def list_inventory(
    city:       str | None = None,
    blood_type: str | None = None,
    db: Session = Depends(get_db)
):
    """List blood inventory across hospitals."""
    query = db.query(models.Inventory)
    if city:
        query = query.filter(models.Inventory.city.ilike(f"%{city}%"))
    if blood_type:
        query = query.filter(models.Inventory.blood_type == blood_type)
    return query.all()


@app.post("/inventory", response_model=schemas.InventoryResponse, status_code=status.HTTP_201_CREATED, tags=["Inventory"])
def add_inventory(payload: schemas.InventoryCreate, db: Session = Depends(get_db)):
    """Add or update inventory for a hospital."""
    # Check if an entry already exists for this hospital + blood type
    existing = db.query(models.Inventory).filter(
        models.Inventory.hospital_name == payload.hospital_name,
        models.Inventory.blood_type    == payload.blood_type,
    ).first()

    if existing:
        existing.units_available = payload.units_available
        existing.updated_at      = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    inventory = models.Inventory(**payload.model_dump())
    db.add(inventory)
    db.commit()
    db.refresh(inventory)
    return inventory
