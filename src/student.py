from maxapi.types import MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton

from config import DEPARTMENTS, ANSWER_WORKERS, find_query_by_id


async def menuSelectDepartment(event: MessageCreated, uni: dict) -> None:
    """
    Меню выбора кафедры/отделения для студента.
    """
    builder = InlineKeyboardBuilder()

    departments = DEPARTMENTS.get(uni["ВУЗ"], [])
    if not departments:
        await event.message.answer(
            text=f"Для вашего ВУЗа ({uni['ВУЗ']}) список кафедр не задан."
        )
        return

    for department in departments:
        builder.row(
            CallbackButton(
                text=department,
                payload=f"newQuestFor_{department}"
            )
        )
    builder.row(
        CallbackButton(text="Мои ответы", payload="student_view_answers")
    )

    await event.message.answer(
        text="Выберите кафедру:",
        attachments=[builder.as_markup()]
    )



async def show_answers_for_student(event, student_user: dict) -> None:
    answers = [a for a in ANSWER_WORKERS if a["id_stud"] == student_user["id"]]
    if not answers:
        await event.message.answer(text="Ответов на ваши вопросы пока нет.")
        return
    for a in answers:
        q = find_query_by_id(a["id_query"])
        await event.message.answer(
            text=(
                f"📬 Ответ на вопрос №{a['id_query']}\n"
                f"«{q['Вопрос'] if q else '—'}»\n\n"
                f"💬 {a['response']}"
            )
        )