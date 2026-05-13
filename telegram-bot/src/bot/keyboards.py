from typing import Literal

from enum import StrEnum
from uuid import UUID

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.core.entities.course import Module
from src.core.entities.student import Group
from src.core.entities.user import UserRole
from src.settings import settings


class UserChoiceCbData(CallbackData, prefix="role_choice"):
    role: UserRole


def get_role_choice_kb() -> InlineKeyboardMarkup:
    """Inline клавиатура для выбора роли"""

    builder = InlineKeyboardBuilder()
    builder.button(
        text="🧑🏻‍🎓 Студент", callback_data=UserChoiceCbData(role=UserRole.STUDENT).pack()
    )
    builder.button(
        text="🧑🏻‍🏫 Преподаватель", callback_data=UserChoiceCbData(role=UserRole.TEACHER).pack()
    )
    builder.adjust(1)
    return builder.as_markup()


class GroupChoiceCbData(CallbackData, prefix="group_choice"):
    group_id: UUID


def get_group_choice_kb(groups: list[Group]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора группы"""

    builder = InlineKeyboardBuilder()
    for group in groups:
        builder.button(
            text=group.title, callback_data=GroupChoiceCbData(group_id=group.id).pack()
        )
    builder.adjust(1)
    return builder.as_markup()


class ConfirmSignUpCbData(CallbackData, prefix="confirm_signup"):
    action: Literal["ok", "cancel"] = "ok"


def get_confirm_sign_up_kb() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения регистрации на курс"""

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Всё верно", callback_data=ConfirmSignUpCbData().pack())
    builder.button(text="❌ Отмена", callback_data=ConfirmSignUpCbData(action="cancel").pack())
    return builder.as_markup()


class ModuleCbData(CallbackData, prefix="module"):
    module_id: UUID


def get_modules_kb(modules: list[Module], current_module_id: UUID) -> InlineKeyboardMarkup:
    """Клавиатура со списком модулей курса"""

    current_order = next(
        (order for order, module in enumerate(modules) if module.id == current_module_id), None
    )
    builder = InlineKeyboardBuilder()
    for order, module in enumerate(modules):
        if current_order is not None and order <= current_order:
            btn_text = f"🟢 {module.title}"
        else:
            btn_text = f"🔴 {module.title}"
        builder.button(
            text=btn_text, callback_data=ModuleCbData(module_id=module.id).pack()
        )
    builder.adjust(1)
    return builder.as_markup()


class ModuleAction(StrEnum):
    STUDY_THEORY = "study_theory"
    TAKE_TEST = "take_test"
    START_TASK = "start_task"


class ModuleStudyCbData(CallbackData, prefix="module_study"):
    id: UUID
    action: ModuleAction


def get_module_study_kb(
        course_id: UUID, module_id: UUID, user_id: int, is_test_passed: bool = False
) -> InlineKeyboardMarkup:
    """Клавиатура для изучения модуля"""

    builder = InlineKeyboardBuilder()
    web_app_url = (
        f"{settings.app.url}/students"
        f"/courses/{course_id}"
        f"/modules/{module_id}"
        f"/theory?user_id={user_id}"
    )
    builder.button(text="📖 Изучить теорию", web_app=WebAppInfo(url=web_app_url))
    if not is_test_passed:
        builder.button(
            text="🎯 Пройти тестирование",
            callback_data=ModuleStudyCbData(id=module_id, action=ModuleAction.TAKE_TEST).pack()
        )
    if is_test_passed:
        builder.button(
            text="🧪 Выполнить задание",
            callback_data=ModuleStudyCbData(
                id=module_id, action=ModuleAction.START_TASK
            ).pack()
        )
    builder.adjust(1)
    return builder.as_markup()


class StartTestCbData(CallbackData, prefix="start_test"):
    action: Literal["start", "cancel"] = "start"


class SkipTestCbData(CallbackData, prefix="skip_test"):
    action: str


def get_start_test_kb() -> InlineKeyboardMarkup:
    """Клавиатура для начала тестирования"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🏁 Начать тестирование", callback_data=StartTestCbData().pack())
    builder.button(text="❌ Отмена", callback_data=StartTestCbData(action="cancel").pack())
    builder.button(
        text="⏩ Пропустить тест", callback_data=SkipTestCbData(action="skip").pack()
    )
    return builder.as_markup()


class OptionChoiceCbData(CallbackData, prefix="option_choice"):
    index: int


def get_options_choice_kb(options: list[str]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора вариантов ответа"""

    builder = InlineKeyboardBuilder()
    for i in range(len(options)):
        builder.button(text=f"{i + 1}", callback_data=OptionChoiceCbData(index=i).pack())
    builder.adjust(1)
    return builder.as_markup()


class TaskCbData(CallbackData, prefix="task"):
    action: Literal["finish"] = "finish"


def get_finish_task_kb() -> InlineKeyboardMarkup:
    """Клавиатура для завершения практического задания"""

    builder = InlineKeyboardBuilder()
    builder.button(text="🏁 Завершить", callback_data=TaskCbData().pack())
    return builder.as_markup()
