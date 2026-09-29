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
from gigachat_service import get_faq_answer

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


# -------- Оценка ответа GigaChat --------
@dp.message_callback(F.callback.payload == "ai_satisfied")
async def handle_ai_satisfied(event: MessageCallback):
    user_id = event.callback.user.user_id
    session = state.get_session(user_id)

    if session and session.get("mode") == "evaluating_ai":
        state.clear_session(user_id)
        await event.message.answer(text="Рады были помочь! Если появятся еще вопросы, обращайтесь.")
    else:
        await event.message.answer(text="Действие устарело.")


@dp.message_callback(F.callback.payload == "ai_forward")
async def handle_ai_forward(event: MessageCallback):
    user_id = event.callback.user.user_id
    session = state.get_session(user_id)

    if session and session.get("mode") == "evaluating_ai":
        id_ask = session.get("id_ask")
        text = session.get("last_question")
        department = session.get("depart")

        # Сохраняем вопрос в базу данных к живым сотрудникам
        save_query(
            id_query=id_ask,
            id_stud=user_id,
            department=department,
            query=text,
        )

        state.clear_session(user_id)
        print_query()
        await event.message.answer(text="✅ Ваш вопрос перенаправлен. Ожидайте ответа от сотрудника деканата.")
    else:
        await event.message.answer(text="Действие устарело.")


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
# ============================================================
# Суперпользователь (SU) — режим активируется командой "su"
# ============================================================


# ID тех, кому разрешён вход в SU-режим.
# Если список пустой — пускаем любого (удобно для отладки).
SUPERUSER_IDS: set[int] = {
    # 123456789,
}


def is_superuser(user_id: int) -> bool:
    """Пускаем всех, если список пустой — иначе только указанные ID."""
    if not SUPERUSER_IDS:
        return True
    return user_id in SUPERUSER_IDS


async def su_menu(event: MessageCreated) -> None:
    """Главное меню суперпользователя."""
    builder = InlineKeyboardBuilder()
    builder.row(
        CallbackButton(text="Очистить мой ID из БД", payload="su_clear_me"),
    )
    builder.row(
        CallbackButton(text="Информация о кафедре", payload="su_department"),
    )
    builder.row(
        CallbackButton(text="Информация о студентах", payload="su_students"),
    )
    builder.row(
        CallbackButton(text="Показать записи из БД", payload="su_dump"),
    )
    builder.row(
        CallbackButton(text="Выйти из SU", payload="su_exit"),
    )

    await event.message.answer(
        text="🔧 Режим суперпользователя.\nВыберите действие:",
        attachments=[builder.as_markup()],
    )


async def su_command(event: MessageCreated, text: str) -> None:
    """Обработка текстовых команд внутри SU-режима."""
    user_id = event.message.sender.user_id

    if text.lower() in {"exit", "выход", "su_exit"}:
        state.exit_su(user_id)
        await event.message.answer(text="Вы вышли из режима суперпользователя.")
        await show_start_menu(event)
        return

    await event.message.answer(
        text="Используйте кнопки меню или напишите 'exit' для выхода."
    )


# ============================================================
# Callback-обработчики SU-кнопок
# ============================================================
@dp.message_callback(F.callback.payload == "su_clear_me")
async def su_clear_me(event: MessageCallback) -> None:
    user_id = event.user.user_id  # проверьте поле под вашу версию maxapi
    # delete_user(user_id)          # ваша функция удаления из БД
    state.exit_su(user_id)
    await event.answer(
        text="✅ Ваш ID удалён из БД. Можно регистрироваться заново.",
        show_alert=True,
    )


@dp.message_callback(F.callback.payload == "su_department")
async def su_department(event: MessageCallback) -> None:
    # info = get_department_info()  # ваша функция
    await event.answer(text=f"Информация о кафедре:\n{"info"}", show_alert=True)


@dp.message_callback(F.callback.payload == "su_students")
async def su_students(event: MessageCallback) -> None:
    # info = get_students_info()  # ваша функция
    await event.answer(text=f"Информация о студентах:\n{"info"}", show_alert=True)


@dp.message_callback(F.callback.payload == "su_dump")
async def su_dump(event: MessageCallback) -> None:
    # records = dump_some_records()  # ваша функция
    await event.answer(text=f"Записи из БД:\n{"records"}", show_alert=True)


@dp.message_callback(F.callback.payload == "su_exit")
async def su_exit(event: MessageCallback) -> None:
    user_id = event.user.user_id
    state.exit_su(user_id)
    await event.answer(text="Вы вышли из режима суперпользователя.", show_alert=True)


# ============================================================
# Единый роутер текстовых сообщений
# ============================================================
@dp.message_created(lambda m: m.message.body and m.message.body.text)
async def router(event: MessageCreated) -> None:
    user_id = event.message.sender.user_id
    text = event.message.body.text.strip()

    # 1. Вход в SU
    if text.lower() == "su":
        if not is_superuser(user_id):
            await event.message.answer(text="⛔ Нет доступа.")
            return
        state.enter_su(user_id)
        await su_menu(event)
        return

    # 2. Уже в SU — обрабатываем только SU-команды
    if state.is_su(user_id):
        await su_command(event, text)
        return

    # 3. Обычная логика
    await echo(event)


# ============================================================
# Основной обработчик (переименован из echo, БЕЗ декоратора!)
# ============================================================

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

        save_answer(
            id_query=id_query,
            id_stud=q["id_stud"],
            id_worker=user_id,
            response=text,
        )

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

        # Проверяем, есть ли шаблонный ответ
        ai_answer = get_faq_answer(text)

        if ai_answer:
            # Сохраняем вопрос и меняем статус сессии ожидания ответа
            session["mode"] = "evaluating_ai"
            session["last_question"] = text

            # Создаем кнопки
            builder = InlineKeyboardBuilder()
            builder.row(
                CallbackButton(text="✅ Да, спасибо!", payload="ai_satisfied"),
                CallbackButton(text="❌ Нет, нужен сотрудник", payload="ai_forward")
            )

            await event.message.answer(
                text=f"🤖 Быстрый ответ:\n\n{ai_answer}\n\nВы удовлетворены ответом?",
                attachments=[builder.as_markup()]
            )
            return
        # -------------------------------

        # Если ответа нет в FAQ, продолжаем стандартную логику и отправляем живым работникам
        id_ask = session.get("id_ask")
        save_query(
            id_query=id_ask,
            id_stud=user_id,
            department=session.get("depart"),
            query=text,
        )

        state.clear_session(user_id)
        print_query()  # отладочный вывод (можно убрать в проде)
        await event.message.answer(text="✅ Вопрос добавлен в очередь на рассмотрение сотрудникам.")
        return

        ai_answer = get_faq_answer(text)

        if ai_answer:
            state.clear_session(user_id)
            await event.message.answer(text=f"Быстрый ответ:\n\n{ai_answer}")
            return

        id_ask = session.get("id_ask")
        save_query(
            id_query=id_ask,
            id_stud=user_id,
            department=session.get("depart"),
            query=text,
        )

        state.clear_session(user_id)
        print_query()
        await event.message.answer(
            text="✅ Вопрос добавлен в очередь на рассмотрение сотрудникам."
        )
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