from enum import StrEnum

from aiogram.filters.callback_data import CallbackData

from ..core import enums


class StartCBData(CallbackData, prefix="start"):
    tg_user_id: int


class MenuAction(StrEnum):
    CREATE_COURSE = "create_course"


class MenuCBData(CallbackData, prefix="menu"):
    user_id: int
    action: MenuAction


class FormAction(StrEnum):
    NEXT = "next"
    PREVIOUS = "previous"
    SKIP = "skip"


class FormNavigationCBData(CallbackData, prefix="form_nav"):
    action: FormAction
    current_step: str | None = None


class DifficultyLevelCBData(CallbackData, prefix="difficulty_level"):
    level: enums.DifficultyLevel
