from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_audio = State()
    waiting_for_manager = State()
