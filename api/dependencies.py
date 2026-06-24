from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from repositories.task_repo import TaskRepository
from services.task_service import TaskService

async def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    repo = TaskRepository(db)
    return TaskService(repo)

async def get_current_user():
    return {"id": 42, "role": "Contractor", "company_id": 1}