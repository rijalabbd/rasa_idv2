from sqlalchemy import Column, Integer, String, Float
from app.db.base import Base


class TKPIFood(Base):
    """Indonesian Food Composition (TKPI) table."""
    
    __tablename__ = "tkpi_foods"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    tkpi_code = Column(String(32), unique=True, index=True, nullable=True)
    
    # Macronutrients (per 100g) — nullable for incomplete seed data
    energi_kal = Column(Float, nullable=True)
    protein_g = Column(Float, nullable=True)
    lemak_g = Column(Float, nullable=True)
    karbo_g = Column(Float, nullable=True)
    serat_g = Column(Float, nullable=True)
    
    def __repr__(self) -> str:
        return f"<TKPIFood(id={self.id}, name='{self.name}', code='{self.tkpi_code}')>"
