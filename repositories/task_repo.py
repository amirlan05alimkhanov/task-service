from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.task import Task

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: int) -> Task:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def get_available_by_company(self, company_id: int):
        """Свободные задачи для ленты исполнителей"""
        result = await self.db.execute(
            select(Task).where(Task.company_id == company_id, Task.status == "created")
        )
        return result.scalars().all()

    async def get_all_by_company(self, company_id: int):
        """Вообще все задачи организации для панели менеджера"""
        result = await self.db.execute(
            select(Task).where(Task.company_id == company_id)
        )
        return result.scalars().all()

    async def create(self, task: Task) -> Task:
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def delete(self, task: Task):
        """Физическое удаление задачи из СУБД"""
        await self.db.delete(task)
        await self.db.commit()

    async def save_changes(self):
        await self.db.commit()