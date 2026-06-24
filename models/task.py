from sqlalchemy import Column, Integer, String, Numeric, DateTime, func
from database.connection import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    budget = Column(Numeric(10, 2), nullable=False)
    status = Column(String(50), default="created")  # created, accepted, completed

    company_id = Column(Integer, nullable=False)
    contractor_id = Column(Integer, nullable=True)
    contract_id = Column(Integer, nullable=True)  # ID из внешнего микросервиса Contracts

    created_at = Column(DateTime, server_default=func.now())