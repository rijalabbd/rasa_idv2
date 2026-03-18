from pydantic import BaseModel
from typing import Optional
from app.schemas.common import NutritionInfo


class TKPISearchItem(BaseModel):
    """TKPI search result item."""
    id: int
    tkpi_code: Optional[str] = None
    name: str
    energi_kal: Optional[float] = None
    protein_g: Optional[float] = None
    lemak_g: Optional[float] = None
    karbo_g: Optional[float] = None
    serat_g: Optional[float] = None
    
    class Config:
        from_attributes = True


class TKPIDetail(BaseModel):
    """TKPI detail with full nutrition information."""
    id: int
    name: str
    nutrition: NutritionInfo
    
    class Config:
        from_attributes = True
