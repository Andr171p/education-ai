from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..core.enums import DifficultyLevel
from .callbacks import (
    DifficultyLevelCBData,
    FormAction,
    FormNavigationCBData,
    MenuAction,
    MenuCBData,
)

"""
def start_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Создать курс", web_app=WebAppInfo(url=f"{settings.ngrok.url}/courses/create")
    )
    return builder.as_markup()
"""


def start_kb(user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎓 Создать курс", callback_data=MenuCBData(
            user_id=user_id, action=MenuAction.CREATE_COURSE
        ).pack()
    )
    return builder.as_markup()


def difficulty_level_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    text_to_level_map = {
        ("🥉 Начинающий", DifficultyLevel.BEGINNER),
        ("🥈 Средний", DifficultyLevel.INTERMEDIATE),
        ("🥇 Продвинутый", DifficultyLevel.ADVANCED),
        ("🏆 Профессиональный", DifficultyLevel.EXPERT)
    }
    for text_to_level in text_to_level_map:
        text, level = text_to_level
        builder.button(text=text, callback_data=DifficultyLevelCBData(level=level).pack())
    builder.adjust(1)
    return builder.as_markup()


def form_navigation_kb(current_step: str, can_skip: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if can_skip:
        builder.button(
            text="⏭️ Пропустить",
            callback_data=FormNavigationCBData(
                action=FormAction.SKIP, current_step=current_step
            ).pack(),
        )
    builder.button(
        text="↩️ Назад",
        callback_data=FormNavigationCBData(
            action=FormAction.PREVIOUS, current_step=current_step
        ).pack(),
    )
    builder.adjust(1)
    return builder.as_markup()
