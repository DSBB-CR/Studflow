from maxapi.types import MessageCreated
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import CallbackButton

from config import DEPARTMENTS


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
                payload=f"dept_{department}"
            )
        )

    await event.message.answer(
        text="Выберите кафедру:",
        attachments=[builder.as_markup()]
    )