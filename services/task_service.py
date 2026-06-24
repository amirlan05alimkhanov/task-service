import httpx
from fastapi import HTTPException
from repositories.task_repo import TaskRepository
from models.task import Task
from schemas.task import TaskCreate

# Базовые URL микросервисов (без путей эндпоинтов)
CONTRACTS_SERVICE_URL = "http://localhost:8002/api/v1/contracts"
NOTIFICATIONS_SERVICE_URL = "http://localhost:8003/api/v1/notifications"


class TaskService:
    def __init__(self, repo: TaskRepository):
        self.repo = repo

    async def create_new_task(self, payload: TaskCreate, company_id: int) -> Task:
        new_task = Task(**payload.model_dump(), company_id=company_id, status="created")
        return await self.repo.create(new_task)

    async def list_available_tasks(self, company_id: int):
        return await self.repo.get_available_by_company(company_id)

    async def accept_task(self, task_id: int, contractor_id: int, company_id: int) -> Task:
        # 1. Быстро читаем задачу из БД
        task = await self.repo.get_by_id(task_id)

        if not task:
            raise HTTPException(status_code=404, detail="Задача не найдена")
        if task.status != "created":
            raise HTTPException(status_code=400, detail="Задача уже кем-то принята")
        if task.company_id != company_id:
            raise HTTPException(status_code=403, detail="Нет доступа к этой компании")

        # 2. Внешний сетевой запрос к сервису Контрактов
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
                # Заглушка, если contracts-service еще не запущен
                contract_id = 777

        # 3. Применяем все изменения к объекту разом
        task.contractor_id = contractor_id
        task.status = "accepted"
        task.contract_id = contract_id

        # 4. Сохраняем состояние задачи в локальной БД (Один быстрый коммит)
        await self.repo.save_changes()

        # 5. ИНТЕГРАЦИЯ: Отправляем запрос в микросервис Notifications
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{NOTIFICATIONS_SERVICE_URL}/send",  # <--- Исправили путь к роутеру
                    json={
                        "user_id": 1,  # Шлем менеджеру с ID 1, чтобы увидеть в GET-запросе уведомлений
                        "message": f"Исполнитель {contractor_id} принял задачу #{task.id} ('{task.title}').",
                        "notification_type": "task_accepted"  # <--- Переименовали в notification_type
                    },
                    timeout=2.0
                )
            except httpx.RequestError:
                # Если сервис уведомлений недоступен, логика тасков все равно успешно завершится
                pass

        return task