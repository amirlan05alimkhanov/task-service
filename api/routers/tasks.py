from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from schemas.task import TaskCreate, TaskResponse
from services.task_service import TaskService
from api.dependencies import get_task_service, get_current_user

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, service: TaskService = Depends(get_task_service)):
    task = await service.create_new_task(payload, company_id=1)
    return TaskResponse.model_validate(task)


@router.get("", response_model=List[TaskResponse])
async def get_tasks(user: dict = Depends(get_current_user), service: TaskService = Depends(get_task_service)):
    return await service.list_available_tasks(user["company_id"])


@router.post("/{task_id}/accept", response_model=TaskResponse)
async def accept_task(
        task_id: int,
        user: dict = Depends(get_current_user),
        service: TaskService = Depends(get_task_service)
):
    if user["role"] != "Contractor":
        raise HTTPException(status_code=403, detail="Только исполнители могут принимать задачи")

    task = await service.accept_task(task_id, user["id"], user["company_id"])

    return TaskResponse.model_validate(task)