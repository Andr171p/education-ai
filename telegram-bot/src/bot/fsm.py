from aiogram.fsm.state import State, StatesGroup


class CourseCreationForm(StatesGroup):
    """Форма для создания курса"""

    discipline = State()
    target_audience = State()
    difficulty_level = State()
    estimated_duration_hours = State()
    files = State()
    external_links = State()
    comment = State()
