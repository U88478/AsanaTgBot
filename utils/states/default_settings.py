from aiogram.fsm.state import State, StatesGroup

class DefaultSettings(StatesGroup):
    workspace = State()
    project = State()
    section = State()