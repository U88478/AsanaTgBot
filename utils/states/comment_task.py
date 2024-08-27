from aiogram.fsm.state import State, StatesGroup


class CommentTask(StatesGroup):
    Comment = State()
