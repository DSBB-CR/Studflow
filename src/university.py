from maxapi.types import MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton


async def menuSelectWorker(event: MessageCreated, worker: dict) -> None:
    """
    Меню работника университета.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        CallbackButton(
            text="Посмотреть вопросы к кафедре",
            payload="workers_view_questions"
        )
    )

    await event.message.answer(
        text=f"Выберите действие, {worker['Имя']}:",
        attachments=[builder.as_markup()]
    )