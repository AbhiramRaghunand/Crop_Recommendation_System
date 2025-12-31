from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from database.farmer import Farmer
from utils.auth import get_current_farmer
from database.database import get_db
from database.suitability import SuitabilityHistory

router = APIRouter(prefix="/suitability-history")

@router.get("/")
async def get_history(db: Session = Depends(get_db),
                      authorization: str = Header(default=None),
                      user = Depends(get_current_farmer)):

    # get farmer for the current user
    farmer = db.query(Farmer).filter(Farmer.user_id == user.id).first()
    if not farmer:
        return []

    history = (
        db.query(SuitabilityHistory)
        .filter(SuitabilityHistory.farmer_id == farmer.id)   # FIXED
        .order_by(SuitabilityHistory.created_at.desc())
        .limit(3)
        .all()
    )

    return history

