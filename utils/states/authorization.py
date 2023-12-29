from aiogram.fsm.state import State, StatesGroup

class Authorization(StatesGroup):
    token = State()