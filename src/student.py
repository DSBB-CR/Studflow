from maxapi.types import MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton

from config import DEPARTMENTS
from dataBase.query import find_queries_for_student


async def menuSelectDepartment(event: MessageCreated, uni: dict) -> None:
    builder = InlineKeyboardBuilder()
    departments = DEPARTMENTS.get(uni["ВУЗ"], [])
    if not departments:
        await event.message.answer(text=f"Для вашего ВУЗа ({uni['ВУЗ']}) список кафедр не задан.")
        return
    for department in departments:
        builder.row(CallbackButton(text=department, payload=f"newQuestFor_{department}"))
    builder.row(CallbackButton(text="Мои ответы", payload="student_view_answers"))
    await event.message.answer(text="Выберите кафедру:", attachments=[builder.as_markup()])


async def show_answers_for_student(event, student_user: dict) -> None:
    answers = find_queries_for_student(student_user["id"])
    if not answers:
        await event.message.answer(text="Ответов на ваши вопросы пока нет.")
        return
    for a in answers:
        await event.message.answer(
            text=(
                f"📬 Ответ на вопрос №{a['id_query']}\n"
                f"«{a['Вопрос']}»\n\n"
                f"💬 {a['answer_text']}"
            )
        )