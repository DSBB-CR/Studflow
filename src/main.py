# std
import asyncio
import logging
from random import randint

# maxapi import
from maxapi import Bot, F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

# gigachat import forewer
from gigachat import GigaChat

# local import func and constants
from bot import dp
from globParams import state
from dataBase.query import goToJsonStudent, goToJsonWorker, find_user, dataBaseDEMO
from config import (
    UNIVERSITIES,
    find_query_by_id,
    save_answer,
    save_query,
    print_query,
    QUERY_STUDENTS,
    MAX_TOKEN,
    GIGACHAT_KEY
)

# local import file
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

async def notify_student(id_stud: int, q: dict, answer: str) -> None:
    """
    Отправляет студенту ответ работника вуза.
    Если не получилось — просто логируем (студент может быть не в чате с ботом).
    """
    try:
        await bot.send_message(
            user_id=id_stud,
            text=(
                f"📬 Ответ на ваш вопрос №{q['id_query']}\n"
                f"«{q['Вопрос']}»\n\n"
                f"💬 {answer}"
            ),
        )
    except Exception as e:
        logging.warning(f"Не удалось отправить ответ студенту {id_stud}: {e}")


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

@dp.message_callback(F.callback.payload == "student_view_answers")
async def student_view_answers(event: MessageCallback):
    user_id = event.callback.user.user_id
    student_user = find_user(user_id)
    if student_user is None or student_user["status"] != "student":
        await event.message.answer(text="Вы не зарегистрированы как студент.")
        return
    await student.show_answers_for_student(event, student_user)

# ============================================================
# Callback-хендлеры работников вуза
# ============================================================

@dp.message_callback(F.callback.payload == "workers_view_questions")
async def workers_view_questions(event: MessageCallback):
    user_id = event.callback.user.user_id
    worker = find_user(user_id)

    if worker is None or worker["status"] != "worker":
        await event.message.answer(text="Вы не зарегистрированы как работник вуза.")
        return

    await university.show_queries_for_worker(event, worker)


@dp.message_callback(F.callback.payload.startswith("answer_"))
async def handle_answer_button(event: MessageCallback):
    user_id = event.callback.user.user_id
    worker = find_user(user_id)

    if worker is None or worker["status"] != "worker":
        await event.message.answer(text="Вы не зарегистрированы как работник вуза.")
        return

    # payload вида "answer_1111"
    try:
        id_query = int(event.callback.payload.split("_", 1)[1])
    except (IndexError, ValueError):
        await event.message.answer(text="Некорректный вопрос.")
        return

    q = find_query_by_id(id_query)
    if q is None:
        await event.message.answer(text="Вопрос не найден.")
        return

    # Проверяем, что вопрос действительно к кафедре работника
    if q["ВУЗ"] != worker["ВУЗ"].upper() or q["Кафедра"] != worker["Кафедра"].lower():
        await event.message.answer(text="Этот вопрос не к вашей кафедре.")
        return

    # Запоминаем, что работник сейчас отвечает на этот вопрос
    state.start_answer(user_id, id_query)

    await event.message.answer(
        text=(
            f"✍️ Введите ответ на вопрос №{id_query}:\n"
            f"«{q['Вопрос']}»\n\n"
            f"Для отмены введите /cancel"
        )
    )

# -------- Отмена ответа --------
@dp.message_created(Command("cancel"))
async def cancelAnswer_command(event: MessageCreated):
    user_id = event.message.sender.user_id
    if state.get_session(user_id):
        state.clear_session(user_id)
        await event.message.answer(text="Действие отменено.")
    else:
        await event.message.answer(text="Нечего отменять.")


# ============================================================
# Обработка ввода вопроса студента
# ============================================================


@dp.message_callback(F.callback.payload.startswith("newQuestFor_"))
async def handle_quests_button(event: MessageCallback):
    user_id = event.callback.user.user_id
    stud = find_user(user_id)

    if stud is None or stud["status"] != "student":
        await event.message.answer(text="Вы не зарегистрированы как студент вуза.")
        return

    id_query = randint(0, 100_000_000)
    state.start_asking(user_id, id_query, event.callback.payload.split("_", 1)[1])

    await event.message.answer(
        text=(
            f"✍️ Введите вопрос №{id_query}:\n"
            f"Для отмены введите /cancel_query"
        )
    )

# -------- Отмена вопроса --------
@dp.message_created(Command("cancel_query"))
async def cancelQuery_command(event: MessageCreated):
    user_id = event.message.sender.user_id
    if state.get_session(user_id):
        state.clear_session(user_id)
        await event.message.answer(text="Действие отменено.")
    else:
        await event.message.answer(text="Нечего отменять.")

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
    text = event.message.body.text.strip()

    # 0. Пользователь отвечает на вопрос студента
    session = state.get_session(user_id)
    if session and session.get("mode") == "answering":
        worker = find_user(user_id)
        if worker is None:
            state.clear_session(user_id)
            await show_start_menu(event)
            return

        id_query = session["id_query"]
        q = find_query_by_id(id_query)
        if q is None:
            state.clear_session(user_id)
            await event.message.answer(text="Вопрос не найден.")
            return

        # Сохраняем ответ
        save_answer(
            id_query=id_query,
            id_stud=q["id_stud"],
            id_worker=user_id,
            response=text,
        )

        # Отправляем студенту ответ (если он есть в БД и это возможно)
        await notify_student(q["id_stud"], q, text)

        state.clear_session(user_id)
        await event.message.answer(text="✅ Ответ отправлен студенту.")
        return

    # 1. Студен задает вопрос
    session = state.get_session(user_id)
    if session and session.get("mode") == "asking":
        stud = find_user(user_id)
        if stud is None:
            state.clear_session(user_id)
            await show_start_menu(event)
            return

        
        id_ask = session.get("id_ask")
        # Сохраняем Вопрос
        save_query(
            id_query=id_ask,
            id_stud=user_id,
            department=session.get("depart"),
            query=text,
        )
        
        # Отправляем вопрос студента (если это возможно)

        state.clear_session(user_id)
        print_query()
        await event.message.answer(text="✅ Вопрос добавлен в очередь на рассмотрение.")
        return

    # 2. Идёт регистрация?
    if state.registration_open:
        await handle_registration(event)
        return

    # 3. Пользователь уже есть в БД — показываем его меню
    user = find_user(user_id)
    if user is not None:
        if user["status"] == "student":
            await student.menuSelectDepartment(event, user)
        elif user["status"] == "worker":
            await university.menuSelectWorker(event, user)
        return

    # 3. Незнакомый — стартовое меню
    await show_start_menu(event)


# ============================================================
# Обработчик текстовых сообщений (GigaChat)
# ============================================================

# @dp.message()
# async def handle_message(event: MessageCreated):
#     # Инициализируем клиент GigaChat с вашим ключом из .env
#     with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
#             # Передаем текст от пользователя (message.text) в нейросеть
#         response = giga.chat(event)

#             # Получаем сгенерированный текст из ответа
#         ai_answer = response.choices[0].message.content

#     # Бот отправляет ответ нейросети обратно пользователю
#     await event.message.answer(ai_answer)

# ============================================================
# Точка входа
# ============================================================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())