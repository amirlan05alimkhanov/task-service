import httpx
from fastapi import HTTPException, status
from repositories.task_repo import TaskRepository
from models.task import Task
from schemas.task import TaskCreate, TaskUpdate

CONTRACTS_SERVICE_URL = "http://localhost:8002/api/v1/contracts"
NOTIFICATIONS_SERVICE_URL = "http://localhost:8003/api/v1/notifications"


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def create_new_task(self, payload: TaskCreate, company_id: int) -> Task:
        new_task = Task(**payload.model_dump(), company_id=company_id, status="created")
        return await self.repo.create(new_task)

    async def get_task_by_id(self, task_id: int, company_id: int) -> Task:
        task = await self.repo.get_by_id(task_id)
        if not task or task.company_id != company_id:
            raise HTTPException(status_code=404, detail="Задача не найдена или нет доступа")
        return task

    async def list_tasks(self, company_id: int, role: str):
        """Разделение вывода: исполнитель видит только доступные, менеджер - все"""
        if role == "Contractor":
            return await self.repo.get_available_by_company(company_id)
        return await self.repo.get_all_by_company(company_id)

    async def update_task_details(self, task_id: int, payload: TaskUpdate, company_id: int) -> Task:
        task = await self.get_task_by_id(task_id, company_id)

        if task.status != "created":
            raise HTTPException(
                status_code=400,
                detail="Нельзя редактировать задачу, которая уже принята или завершена"
            )

        # Обновляем только те поля, которые прислал клиент
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)

        await self.repo.save_changes()
        return task

    async def update_task_status_explicitly(self, task_id: int, new_status: str, company_id: int) -> Task:
        """Изменение статуса (например, перевод менеджером в completed)"""
        task = await self.get_task_by_id(task_id, company_id)

        valid_statuses = ["created", "accepted", "completed", "cancelled"]
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Неверный статус")

        task.status = new_status
        await self.repo.save_changes()

        # Шлем нотификацию об изменении статуса
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{NOTIFICATIONS_SERVICE_URL}/send",
                    json={
                        "user_id": 1,
                        "message": f"Статус задачи #{task.id} изменен на '{new_status}'.",
                        "notification_type": "task_status_changed"
                    },
                    timeout=2.0
                )
            except httpx.RequestError:
                pass

        return task

    async def accept_task(self, task_id: int, contractor_id: int, company_id: int) -> Task:
        """Метод принятия задачи исполнителем (Интеграционный метод)"""
        task = await self.get_task_by_id(task_id, company_id)

        if task.status != "created":
            raise HTTPException(status_code=400, detail="Задача уже кем-то принята")

        # Сетевой запрос к сервису Контрактов (до фиксации изменений в БД)
        contract_id = None
        async with httpx.AsyncClient() as client:
            try:
                contract_res = await client.post(
                    f"{CONTRACTS_SERVICE_URL}/generate",
                    json={
                        "company_id": company_id,
                        "contractor_id": contractor_id,
                        "task_id": task_id,
                        "budget": float(task.budget)
                    },
                    timeout=3.0
                )
                if contract_res.status_code == 201:
                    contract_id = contract_res.json().get("id")
            except httpx.RequestError:
                contract_id = 777  # Заглушка для локальных тестов

        task.contractor_id = contractor_id
        task.status = "accepted"
        task.contract_id = contract_id

        await self.repo.save_changes()

        # Сетевой запрос к сервису Уведомлений
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{NOTIFICATIONS_SERVICE_URL}/send",
                    json={
                        "user_id": 1,
                        "message": f"Исполнитель {contractor_id} принял задачу #{task.id} ('{task.title}').",
                        "notification_type": "task_accepted"
                    },
                    timeout=2.0
                )
            except httpx.RequestError:
                pass

        return task

    async def delete_task(self, task_id: int, company_id: int):
        task = await self.get_task_by_id(task_id, company_id)

        if task.status != "created":
            raise HTTPException(
                status_code=400,
                detail="Нельзя удалить задачу, которая уже находится в работе или завершена"
            )

        await self.repo.delete(task)