import main
from globParams import registation

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, Command, MessageCallback



@main.dp.message_created()
async def logg_up_new_student(event: MessageCreated):
    registation()
    await event.message.answer(
        text=f"Введите через пробел: ФИО, группу, направление, год поступления, год выпуска, номер студенческого"
    )
    