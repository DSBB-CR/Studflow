# std
import asyncio
import logging
from pathlib import Path

# dotenv — на случай, если config ещё не загрузил
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# maxapi import
from maxapi import Bot, F
from maxapi.types import MessageCreated, Command, MessageCallback
from maxapi.types import CallbackButton
from maxapi.utils.inline_keyboard import InlineKeyboardBuilder

# local import func and constants
from bot import dp
from globParams import state

from config import (
    UNIVERSITIES,
    MAX_TOKEN,
)

from dataBase.query import (
    find_user,
    goToJsonStudent,
    goToJsonWorker,
    find_query_by_id,
    find_queries_for_worker,
    save_answer,
    save_query,
    next_query_id,
    print_query,
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
            "Введите через пробел: ВУЗ, ФИО (Фамилия Имя Отчество), группу, направление, "
            "год поступления, год выпуска, номер студенческого"
        )
    )


@dp.message_callback(F.callback.payload == "workers_click")
async def handle_workers_click(event: MessageCallback):
    state.start_registration("worker")
    await event.message.answer(
        text=(
            "Регистрация работника университета.\n"
            "Введите через пробел: ВУЗ, ФИО (Фамилия Имя Отчество), кафедру, должность"
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
    if (str(q["ВУЗ"]).upper() != str(worker["ВУЗ"]).upper()
            or str(q["Кафедра"]).lower() != str(worker["Кафедра"]).lower()):
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

    id_query = next_query_id()  # атомарный счётчик из Mongo
    department = event.callback.payload.split("_", 1)[1]
    state.start_asking(user_id, id_query, department)

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

    # Пользователь только что записан в Mongo — читаем его оттуда же
    user = find_user(user_id)
    if user is None:
        await event.message.answer(text="Не удалось сохранить регистрацию.")
        return

    await event.message.answer(text="Регистрация успешна!")
    if user["status"] == "worker":
        await university.menuSelectWorker(event, user)
    else:
        await student.menuSelectDepartment(event, user)


# ============================================================
# Стартовые команды
# ============================================================

@dp.message_created(Command("start"))
async def start(event: MessageCreated) -> None:
    await show_start_menu(event)


@dp.message_created(Command("menu"))
async def menu_command(event: MessageCreated) -> None:
    await show_start_menu(event)

@dp.message_created(Command("log_out"))
async def LogOut(event: MessageCreated) -> None:
    """
    команда для выхода из системы для залогиненного пользователя
    нужна только для тестов интерфейса и отладки ее не будет
    в проде или она будет запоролена
    """
    await show_start_menu(event)

@dp.message_created(lambda m: m.message.body and m.message.body.text)
async def Su(event: MessageCreated) -> None:
    """
    Некоторый арсенал команд для супер пользователя выдающийся через меню кнопок
    - отчистить мой id из БД (например для решистрации под другой тип клиента)
    - вывод информации о кафедре
    - вывод информации о студентах
    - вывод нескольких записей из БД
    - выход из su
    """


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

        # Сохраняем ответ в Mongo
        save_answer(
            id_query=id_query,
            id_stud=q["id_stud"],
            id_worker=user_id,
            response=text,
        )

        # Отправляем студенту ответ
        await notify_student(q["id_stud"], q, text)

        state.clear_session(user_id)
        await event.message.answer(text="✅ Ответ отправлен студенту.")
        return

    # 1. Студент задаёт вопрос
    session = state.get_session(user_id)
    if session and session.get("mode") == "asking":
        stud = find_user(user_id)
        if stud is None:
            state.clear_session(user_id)
            await show_start_menu(event)
            return

        id_ask = session.get("id_ask")
        save_query(
            id_query=id_ask,
            id_stud=user_id,
            department=session.get("depart"),
            query=text,
        )

        state.clear_session(user_id)
        print_query()  # отладочный вывод (можно убрать в проде)
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

    # 4. Незнакомый — стартовое меню
    await show_start_menu(event)


# ============================================================
# Точка входа
# ============================================================

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())