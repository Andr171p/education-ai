from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ContentType, Message

from .callbacks import DifficultyLevelCBData, MenuAction, MenuCBData
from .fsm import CourseCreationForm
from .keyboards import difficulty_level_kb, start_kb

router = Router(name=__name__)


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.reply(
        "Привет!",
        reply_markup=start_kb(user_id=message.from_user.id)
    )


@router.callback_query(MenuCBData.filter(F.action == MenuAction.CREATE_COURSE))
async def handle_create_course_cb(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await query.answer("🎓 Введите <b>название дисциплины</b> курса:")
    await state.set_state(CourseCreationForm.discipline)


@router.message(CourseCreationForm.discipline)
async def process_discipline(message: Message, state: FSMContext) -> None:
    await state.update_data(discipline=message.text)
    await message.answer("👥 Опишите <b>целевую аудиторию</b> вашего курса:")
    await state.set_state(CourseCreationForm.target_audience)


@router.message(CourseCreationForm.target_audience)
async def process_target_audience(message: Message, state: FSMContext) -> None:
    await state.update_data(target_audience=message.text)
    await message.answer(
        text="📊 Выберите <b>уровень сложности</b> курса:", reply_markup=difficulty_level_kb()
    )
    await state.set_state(CourseCreationForm.difficulty_level)


@router.callback_query(CourseCreationForm.difficulty_level)
async def process_difficulty(
        query: CallbackQuery, cb_data: DifficultyLevelCBData, state: FSMContext
) -> None:
    await state.update_data(difficulty_level=cb_data.level)
    await query.answer()
    await query.answer("⏱️ Укажите <b>примерную длительность</b> курса в часах:")
    await state.set_state(CourseCreationForm.estimated_duration_hours)


@router.message(CourseCreationForm.estimated_duration_hours)
async def process_duration(message: Message, state: FSMContext) -> None:
    await state.update_data(target_audience=message.text)
    await message.answer(
        "📎 Прикрепите <b>образовательные материалы</b> (документы, презентации):"
    )
    await state.set_state(CourseCreationForm.files)


@router.message(CourseCreationForm.files, F.content_type.in_({ContentType.DOCUMENT}))
async def process_files(
        message: Message, state: FSMContext, album_messages: list[Message] | None = None
) -> None:
    ...


@router.message(CourseCreationForm.external_links)
async def process_external_links(message: Message, state: FSMContext) -> None:
    ...


@router.message(CourseCreationForm.comment)
async def process_comment(message: Message, state: FSMContext) -> None:
    ...
