from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    budget: Decimal

class TaskUpdate(BaseModel):
    """Схема для частичного обновления данных (PUT/PATCH)"""
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[Decimal] = None

class TaskStatusUpdate(BaseModel):
    """Схема строго для перевода задачи по этапам жизненного цикла"""
    status: str  # created, accepted, completed, cancelled

class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    status: str
    budget: Decimal
    company_id: int
    contractor_id: Optional[int] = None
    contract_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True  # Для Pydantic V2