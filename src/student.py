import main
from globParams import registation
from dataBase import query

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import LinkButton, CallbackButton


@main.dp.message_created()
async def logg_up_new_student(event: MessageCreated):
    registation()
    await event.message.answer(
        text=f"Введите через пробел: ВУЗ, ФИО, группу, направление, год поступления, год выпуска, номер студенческого"
    )



@main.dp.message_created()
async def menuSelectDepartment(event: MessageCreated, uni: str):
    """
        Меню для выбора отделения 
        для запроса к нему от студента

    """
    builder = InlineKeyboardBuilder()

    for department in main.departments[uni]:
        builder.row(
            CallbackButton(text=f"{department}", payload="workers_click")
        )

    await event.message.answer(
        text='Выберите действие:',
        attachments=[builder.as_markup()]
    )