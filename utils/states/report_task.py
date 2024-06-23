from aiogram.fsm.state import State, StatesGroup

class ReportTask(StatesGroup):
    TaskName = State()
    Report = State()