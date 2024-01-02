import asyncio
import logging
import sys
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pytz
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.config import *
from bot.bot_instance import bot
from utils.handlers import router, daily_notification
from aiogram import Dispatcher


async def main():
    dp = Dispatcher()
    dp.include_router(router)

    # Створення планувальника
    scheduler = AsyncIOScheduler()

    # Налаштування часової зони
    kiev = pytz.timezone('Europe/Kiev')

    # Додавання завдання
    scheduler.add_job(daily_notification, 'cron', hour=4, minute=57, timezone=kiev)

    # Запуск планувальника
    scheduler.start()

    # Запуск бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
