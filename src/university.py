from maxapi.types import MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton

from dataBase.query import find_queries_for_worker


async def menuSelectWorker(event: MessageCreated, worker: dict) -> None:
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(
            text="Посмотреть вопросы к кафедре",
            payload="workers_view_questions",
        )
    )
    await event.message.answer(
        text=f"Выберите действие, {worker['Имя']}:",
        attachments=[builder.as_markup()],
    )


async def show_queries_for_worker(event: MessageCreated, worker: dict) -> None:
    """
    Показывает работнику список вопросов по его кафедре,
    каждый — с кнопкой «Ответить».
    """
    queries = find_queries_for_worker(worker)

    if not queries:
        await event.message.answer(
            text=f"К кафедре «{worker['Кафедра']}» вопросов пока нет."
        )
        return

    for q in queries:
        builder = InlineKeyboardBuilder()
        builder.row(
            CallbackButton(
                text="Ответить",
                payload=f"answer_{q['id_query']}",
            )
        )
        await event.message.answer(
            text=(
                f"📩 Вопрос №{q['id_query']}\n"
                f"От: {q['Студент']}\n"
                f"Кафедра: {q['Кафедра']}\n"
                f"Вопрос: {q['Вопрос']}"
            ),
            attachments=[builder.as_markup()],
        )