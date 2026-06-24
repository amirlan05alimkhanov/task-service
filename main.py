import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.routers.tasks import router as tasks_router
from database.connection import engine, Base
from models.task import Task  # Гарантируем регистрацию модели


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n[LIFESPAN] Запуск микросервиса. Ожидание готовности СУБД PostgreSQL...")

    db_ready = False
    # Делаем 5 попыток подключиться к базе данных с интервалом в 2 секунды
    for attempt in range(1, 6):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print(f"[LIFESPAN] [ПОПЫТКА {attempt}] База данных успешно инициализирована! Таблицы готовы.\n")
            db_ready = True
            break
        except Exception as e:
            print(
                f"[LIFESPAN] [ПОПЫТКА {attempt}/5] База данных еще инициализируется внутри Docker. Ждем 2 секунды... (Ошибка: {e})")
            await asyncio.sleep(2)

    if not db_ready:
        print("\n" + "!" * 60)
        print("[КРИТИЧЕСКАЯ ОШИБКА]: Не удалось подключиться к БД после 5 попыток.")
        print("Проверьте, запущен ли контейнер и совпадают ли пароли в .env и docker-compose.")
        print("!" * 60 + "\n")

    yield


app = FastAPI(title="Modular Payouts - Tasks Service", lifespan=lifespan)

app.include_router(tasks_router)