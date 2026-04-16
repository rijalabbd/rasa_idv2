from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.services.tkpi_service import search_tkpi_foods, get_tkpi_food_by_id
from app.schemas.tkpi import TKPISearchItem, TKPIDetail
from app.schemas.common import NutritionInfo
from app.core.config import settings


router = APIRouter()


@router.get("/search", response_model=List[TKPISearchItem])
async def search_tkpi(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    fuzzy: Optional[bool] = Query(
        None,
        description=(
            "Enable token-based fuzzy search. "
            "Overrides the TKPI_FUZZY_SEARCH feature flag when provided. "
            "Pass ?fuzzy=false to force exact-phrase mode on a specific request."
        ),
    ),
    db: Session = Depends(get_db)
):
    """
    Search TKPI foods by name.
    Returns minimal information (id, name) for autocomplete/search results.

    Fuzzy mode (token-based) can be controlled globally via the
    TKPI_FUZZY_SEARCH environment variable, or per-request via ?fuzzy=true/false.
    """
    # Per-request param takes priority; fall back to global feature flag
    use_fuzzy = fuzzy if fuzzy is not None else settings.TKPI_FUZZY_SEARCH
    foods = search_tkpi_foods(db, q, limit, fuzzy=use_fuzzy)
    return foods


@router.get("/{food_id}", response_model=TKPIDetail)
async def get_tkpi_detail(
    food_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed TKPI food information including full nutrition data.
    """
    food = get_tkpi_food_by_id(db, food_id)
    
    if not food:
        raise HTTPException(status_code=404, detail=f"TKPI food {food_id} not found")
    
    return TKPIDetail(
        id=food.id,
        name=food.name,
        nutrition=NutritionInfo(
            energi_kal=food.energi_kal,
            protein_g=food.protein_g,
            lemak_g=food.lemak_g,
            karbo_g=food.karbo_g,
            serat_g=food.serat_g
        )
    )
