from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskStatusUpdate
from services.task_service import TaskService
from api.dependencies import get_task_service, get_current_user

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    user: dict = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    if user["role"] != "Manager":
        raise HTTPException(status_code=403, detail="Только менеджеры могут создавать задачи")
    task = await service.create_new_task(payload, company_id=user["company_id"])
    return TaskResponse.model_validate(task)

@router.get("", response_model=List[TaskResponse])
async def get_all_tasks(
    user: dict = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    tasks = await service.list_tasks(user["company_id"], user["role"])
    return [TaskResponse.model_validate(t) for t in tasks]

@router.get("/{task_id}", response_model=TaskResponse)
async def get_single_task(
    task_id: int,
    user: dict = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    task = await service.get_task_by_id(task_id, user["company_id"])
    return TaskResponse.model_validate(task)

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    payload: TaskUpdate,
    user: dict = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    if user["role"] != "Manager":
        raise HTTPException(status_code=403, detail="Только менеджеры могут редактировать задачи")
    task = await service.update_task_details(task_id, payload, user["company_id"])
    return TaskResponse.model_validate(task)

@router.patch("/{task_id}/status", response_model=TaskResponse)
async def change_task_status(
    task_id: int,
    payload: TaskStatusUpdate,
    user: dict = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    if user["role"] != "Manager":
        raise HTTPException(status_code=403, detail="Только менеджеры могут принудительно менять статус")
    task = await service.update_task_status_explicitly(task_id, payload.status, user["company_id"])
    return TaskResponse.model_validate(task)

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

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    user: dict = Depends(get_current_user),
    service: TaskService = Depends(get_task_service)
):
    if user["role"] != "Manager":
        raise HTTPException(status_code=403, detail="Только менеджеры могут удалять задачи")
    await service.delete_task(task_id, user["company_id"])
    return None