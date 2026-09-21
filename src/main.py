import asyncio
import logging

import student
from globParams import registation
from dataBase import query

from maxapi import Bot, Dispatcher, F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder
from maxapi.types import LinkButton, CallbackButton

logging.basicConfig(level=logging.INFO)


univer = {
    "СПБГТУ",
    "СПБГТИ(ТУ)",
    "ЛЭТИ",
    "ИТМО",
    "МГУ",
    "ВШЭ",
    "МИРЭА",
    "ГУАП",
}

departments = {
    "ИТМО" : ["Деканат", "Физра", "Отдел кадров"]
}


in_loggin = {
    "29602091" : "Student",
    "296020911": "Worker",
}


bot = Bot('f9LHodD0cOIaVSSANDgpCm5carq6CNNc4bfPcpGY5oV9G96n1nPuUibuiMiF_0fV5313aAReNCDGCtCWbdgx')
dp = Dispatcher()


@dp.message_callback(F.callback.payload == "info")
async def info_callback(event: MessageCallback):
    await event.message.answer(
        text="Информационное сообщение!"
    )


@dp.message_callback(F.callback.payload == "studCall")
async def handle_stud_click(event: MessageCreated):
    # Логика для кнопки "Студентов"
    await event.message.answer(
        text="Вы выбрали раздел для студентов",
    )
    await student.logg_up_new_student(event)

@dp.message_callback(F.callback.payload == "workers_click")
async def handle_workers_click(event: MessageCallback):
    # Логика для кнопки "Работникам Университетов"
    await event.message.answer(
        text="Вы выбрали раздел для работников университета.",
    )
    


@dp.message_created(Command("none_command"))
async def startMenu(event: MessageCreated):
    """
        Вставить проверку на то что студен уже зарегестрирован
        или работник университета зарегестрирован 
        если нет то вывод инлайн кнопки 
    """


    builder = InlineKeyboardBuilder()

    # Первый ряд: кнопка-ссылка и кнопка с callback
    builder.row(
        CallbackButton(text="Студентам", payload="studCall"),
        CallbackButton(text="Работникам Университетов", payload="workers_click")
    )
    # Второй ряд: ещё одна callback-кнопка
    builder.row(
        CallbackButton(text="Инфо", payload="info")
    )
    
    await event.message.answer(
        text='Выберите действие:',
        attachments=[builder.as_markup()]
    )


@dp.message_created(F.message.body.text)
async def echo(event: MessageCreated) -> None:
    """
        Здесь происходит обработка вводимого пользователем текста
    """
    for stud in query.dataBaseDEMO:
        if stud['id'] == event.message.sender.user_id:
            """
                преход к работе с запросами студента к вузу

            """
            await student.menuSelectDepartment(event, stud["ВУЗ"])
            return

    # блок регистрации пользователя
    if registation.get_status() == True:
        inputInformationNewUser = event.message.body.text.upper().strip()
        userInfo = inputInformationNewUser.split()
        for uni in univer:
            if userInfo[0] == uni:
                userInfo.append(event.message.sender.user_id)
                query.goToJson(userInfo)
                registation()
                return
        await event.message.answer(f"Университет: {userInfo[0]} не найден проверьте корректность ввода или обратитесь в деканат для получения информации о регистрации университета в система Studflow")


    await startMenu(event)
    #await event.message.answer(f"Университет: {inputUser} не найден проверьте корректность ввода или обратитесь в деканат для получения информации о регистрации университета в система Studflow")


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

