from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    budget: Decimal

class TaskResponse(BaseModel):
    id: int
    title: str
    status: str
    budget: Decimal
    company_id: int
    contractor_id: Optional[int] = None
    contract_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True