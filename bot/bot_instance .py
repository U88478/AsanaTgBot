from utils.config import token
from aiogram import Bot


bot = None

def init_bot(token: str):
    global bot
    bot = Bot(token=token)