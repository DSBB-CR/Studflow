import asyncio
import logging

from maxapi import Bot, F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from gigachat import GigaChat

from bot import dp
from config import UNIVERSITIES, QUERY_STUDENTS, MAX_TOKEN, GIGACHAT_KEY
from globParams import state
from dataBase.query import goToJsonStudent, goToJsonWorker, find_user, dataBaseDEMO

import student
import university


logging.basicConfig(level=logging.INFO)


bot = Bot(token=MAX_TOKEN)


# ============================================================
# Кнопки главного меню
# ============================================================

def build_start_menu() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Студентам", payload="studCall"),
        CallbackButton(text="Работникам Университетов", payload="workers_click"),
    )
    builder.row(
        CallbackButton(text="Инфо", payload="info"),
    )
    return builder


async def show_start_menu(event: MessageCreated) -> None:
    await event.message.answer(
        text="Выберите действие:",
        attachments=[build_start_menu().as_markup()],
    )


# ============================================================
# Callback-хендлеры главного меню
# ============================================================

@dp.message_callback(F.callback.payload == "info")
async def info_callback(event: MessageCallback):
    await event.message.answer(text="Информационное сообщение!")


@dp.message_callback(F.callback.payload == "studCall")
async def handle_stud_click(event: MessageCallback):
    state.start_registration("student")
    await event.message.answer(
        text=(
            "Регистрация студента.\n"
            "Введите через пробел: ВУЗ, ФИО, группу, направление, "
            "год поступления, год выпуска, номер студенческого"
        )
    )


@dp.message_callback(F.callback.payload == "workers_click")
async def handle_workers_click(event: MessageCallback):
    state.start_registration("worker")
    await event.message.answer(
        text=(
            "Регистрация работника университета.\n"
            "Введите через пробел: ВУЗ, ФИО, кафедру, должность"
        )
    )

# ============================================================
# Callback-хендлеры работников вуза
# ============================================================

@dp.message_callback(F.callback.payload == "workers_view_questions")
async def workers_view_questions(event: MessageCallback):
    for query in QUERY_STUDENTS:
        await event.message.answer(
                text=(
                    f'Вопрос: {query["Вопрос"]} от студента {query["Студент"]}'
                )
            )


# ============================================================
# Логика регистрации
# ============================================================

async def handle_registration(event: MessageCreated) -> None:
    text = event.message.body.text.upper().strip()
    parts = text.split()
    user_id = event.message.sender.user_id

    if not parts:
        await event.message.answer(text="Пустое сообщение, попробуйте снова.")
        return

    if parts[0] not in UNIVERSITIES:
        await event.message.answer(
            text=(
                f"Университет «{parts[0]}» не найден. "
                "Проверьте корректность ввода или обратитесь в деканат."
            )
        )
        return

    parts.append(user_id)

    if state.registration_role == "worker":
        ok = goToJsonWorker(parts)
        expected_len = 7
    else:
        ok = goToJsonStudent(parts)
        expected_len = 10

    if not ok:
        await event.message.answer(
            text=(
                f"Неверное количество полей: получено {len(parts)}, "
                f"ожидается {expected_len}. Проверьте формат ввода."
            )
        )
        return

    state.stop_registration()
    for elem in dataBaseDEMO:
        #print(elem)
        if int(elem['id']) == int(user_id):
            await event.message.answer(text="Регистрация успешна!")
            if elem['status'] == "worker":
                await university.menuSelectWorker(event, elem)
            else:
                await student.menuSelectDepartment(event, elem)

            return


# ============================================================
# Стартовые команды
# ============================================================

@dp.message_created(Command("start"))
async def start(event: MessageCreated) -> None:
    await show_start_menu(event)


@dp.message_created(Command("menu"))
async def menu_command(event: MessageCreated) -> None:
    await show_start_menu(event)


# ============================================================
# Главный обработчик текстовых сообщений
# ============================================================

@dp.message_created(lambda m: m.message.body and m.message.body.text)
async def echo(event: MessageCreated) -> None:
    user_id = event.message.sender.user_id

    # 1. Идёт регистрация? Обрабатываем ввод.
    if state.registration_open:
        await handle_registration(event)
        return

    # 2. Пользователь уже есть в БД — показываем его меню
    user = find_user(user_id)
    if user is not None:
        if user["status"] == "student":
            await student.menuSelectDepartment(event, user)
        elif user["status"] == "worker":
            await university.menuSelectWorker(event, user)
        return

    # 3. Незнакомый пользователь — показываем стартовое меню
    await show_start_menu(event)

# ============================================================
# Обработчик текстовых сообщений (GigaChat)
# ============================================================

@dp.message()
async def handle_message(message: types.Message):
    # Инициализируем клиент GigaChat с вашим ключом из .env
    with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
            # Передаем текст от пользователя (message.text) в нейросеть
        response = giga.chat(message.text)

            # Получаем сгенерированный текст из ответа
        ai_answer = response.choices[0].message.content

    # Бот отправляет ответ нейросети обратно пользователю
    await message.answer(ai_answer)

# ============================================================
# Точка входа
# ============================================================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())