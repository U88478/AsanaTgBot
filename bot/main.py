import asyncio
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.config import *
from utils.handlers import router
from aiogram import Bot, Dispatcher


async def main():
    bot = Bot(token, parse_mode='HTML')
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
