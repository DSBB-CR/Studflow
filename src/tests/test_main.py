import pytest
from unittest.mock import AsyncMock, MagicMock

import main
from globParams import state
from config import UNIVERSITIES


@pytest.fixture
def mock_event():
    event = MagicMock()
    event.message = MagicMock()
    event.message.answer = AsyncMock()
    event.message.body = MagicMock()
    event.message.body.text = ""
    event.message.sender = MagicMock()
    event.message.sender.user_id = 12345
    event.callback = MagicMock()
    event.callback.user = MagicMock()
    event.callback.user.user_id = 12345
    event.callback.payload = ""
    return event


# ========== notify_student ==========

class TestNotifyStudent:

    @pytest.mark.asyncio
    async def test_sends_message(self, monkeypatch):
        """Отправляет сообщение студенту."""
        mock_send = AsyncMock()
        monkeypatch.setattr("main.bot.send_message", mock_send)

        q = {"id_query": 1111, "Вопрос": "Который час?"}
        await main.notify_student(12345, q, "13:00")

        mock_send.assert_called_once()
        call_args = mock_send.call_args
        assert "1111" in call_args.kwargs["text"]
        assert "13:00" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_handles_exception(self, monkeypatch):
        """Если отправка упала — не падает."""
        mock_send = AsyncMock(side_effect=Exception("Network error"))
        monkeypatch.setattr("main.bot.send_message", mock_send)

        q = {"id_query": 1111, "Вопрос": "?"}
        await main.notify_student(12345, q, "13:00")  # не должно упасть


# ========== menu_command ==========

class TestMenuCommand:

    @pytest.mark.asyncio
    async def test_sends_menu(self, mock_event):
        """Команда /menu отправляет меню."""
        await main.menu_command(mock_event)
        mock_event.message.answer.assert_called_once()


# ========== cancelQuery_command ==========

class TestCancelQueryCommand:

    @pytest.mark.asyncio
    async def test_no_session(self, mock_event):
        """Если сессии нет — сообщение."""
        await main.cancelQuery_command(mock_event)
        call_args = mock_event.message.answer.call_args
        assert "Нечего отменять" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_clears_session(self, mock_event):
        """Если сессия есть — очищает."""
        state.start_asking(12345, 1111, "Деканат")
        await main.cancelQuery_command(mock_event)
        call_args = mock_event.message.answer.call_args
        assert "отменено" in call_args.kwargs["text"]
        assert 12345 not in state.user_sessions


# ========== handle_answer_button ==========

class TestHandleAnswerButton:

    @pytest.fixture
    def worker(self):
        return {"status": "worker", "ВУЗ": "ИТМО", "Кафедра": "Деканат"}

    @pytest.fixture
    def query(self):
        return {
            "id_query": 1111,
            "Вопрос": "Который час?",
            "ВУЗ": "ИТМО",
            "Кафедра": "Деканат",
            "id_stud": 12345,
        }

    @pytest.mark.asyncio
    async def test_not_registered(self, mock_event, monkeypatch):
        """Если не работник — сообщение."""
        monkeypatch.setattr("main.find_user", lambda uid: None)
        mock_event.callback.payload = "answer_1111"
        await main.handle_answer_button(mock_event)
        call_args = mock_event.message.answer.call_args
        assert "не зарегистрированы" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_invalid_payload(self, mock_event, worker, monkeypatch):
        """Если payload битый — сообщение."""
        monkeypatch.setattr("main.find_user", lambda uid: worker)
        mock_event.callback.payload = "answer_abc"
        await main.handle_answer_button(mock_event)
        call_args = mock_event.message.answer.call_args
        assert "Некорректный вопрос" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_query_not_found(self, mock_event, worker, monkeypatch):
        """Если вопрос не найден — сообщение."""
        monkeypatch.setattr("main.find_user", lambda uid: worker)
        monkeypatch.setattr("main.find_query_by_id", lambda qid: None)
        mock_event.callback.payload = "answer_1111"
        await main.handle_answer_button(mock_event)
        call_args = mock_event.message.answer.call_args
        assert "Вопрос не найден" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_wrong_department(self, mock_event, worker, query, monkeypatch):
        """Если вопрос не к кафедре — сообщение."""
        monkeypatch.setattr("main.find_user", lambda uid: worker)
        monkeypatch.setattr("main.find_query_by_id", lambda qid: {**query, "Кафедра": "Физра"})
        mock_event.callback.payload = "answer_1111"
        await main.handle_answer_button(mock_event)
        call_args = mock_event.message.answer.call_args
        assert "не к вашей кафедре" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_starts_answering(self, mock_event, worker, query, monkeypatch):
        """Если всё ок — начинает сессию."""
        monkeypatch.setattr("main.find_user", lambda uid: worker)
        monkeypatch.setattr("main.find_query_by_id", lambda qid: query)
        mock_event.callback.payload = "answer_1111"
        await main.handle_answer_button(mock_event)

        assert state.user_sessions[12345]["mode"] == "answering"
        assert state.user_sessions[12345]["id_query"] == 1111


# ========== handle_quests_button ==========

class TestHandleQuestsButton:

    @pytest.fixture
    def student(self):
        return {"status": "student", "ВУЗ": "ИТМО"}

    @pytest.mark.asyncio
    async def test_not_registered(self, mock_event, monkeypatch):
        """Если не студент — сообщение."""
        monkeypatch.setattr("main.find_user", lambda uid: None)
        mock_event.callback.payload = "newQuestFor_Деканат"
        await main.handle_quests_button(mock_event)
        call_args = mock_event.message.answer.call_args
        assert "не зарегистрированы" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_starts_asking(self, mock_event, student, monkeypatch):
        """Если студент — начинает сессию."""
        monkeypatch.setattr("main.find_user", lambda uid: student)
        mock_event.callback.payload = "newQuestFor_Деканат"
        await main.handle_quests_button(mock_event)

        assert state.user_sessions[12345]["mode"] == "asking"
        assert state.user_sessions[12345]["depart"] == "Деканат"


# ========== echo ==========

class TestEcho:

    @pytest.mark.asyncio
    async def test_answering_mode(self, mock_event, monkeypatch):
        """Пользователь отвечает на вопрос."""
        worker = {"status": "worker", "ВУЗ": "ИТМО", "Кафедра": "Деканат"}
        query = {"id_query": 1111, "Вопрос": "?", "id_stud": 12345}

        state.start_answer(12345, 1111)
        mock_event.message.body.text = "13:00"

        monkeypatch.setattr("main.find_user", lambda uid: worker)
        monkeypatch.setattr("main.find_query_by_id", lambda qid: query)
        mock_save = MagicMock()
        monkeypatch.setattr("main.save_answer", mock_save)
        mock_notify = AsyncMock()
        monkeypatch.setattr("main.notify_student", mock_notify)

        await main.echo(mock_event)

        mock_save.assert_called_once()
        mock_notify.assert_called_once()
        assert 12345 not in state.user_sessions
        call_args = mock_event.message.answer.call_args
        assert "Ответ отправлен" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_asking_mode(self, mock_event, monkeypatch):
        """Студент задаёт вопрос."""
        student = {"status": "student", "ВУЗ": "ИТМО"}
        state.start_asking(12345, 2222, "Деканат")
        mock_event.message.body.text = "Который час?"

        monkeypatch.setattr("main.find_user", lambda uid: student)
        mock_save = MagicMock()
        monkeypatch.setattr("main.save_query", mock_save)
        mock_print = MagicMock()
        monkeypatch.setattr("main.print_query", mock_print)

        await main.echo(mock_event)

        mock_save.assert_called_once()
        assert 12345 not in state.user_sessions
        call_args = mock_event.message.answer.call_args
        assert "Вопрос добавлен" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_registration_mode(self, mock_event, monkeypatch):
        """Идёт регистрация — вызывается handle_registration."""
        state.registration_open = True
        mock_event.message.body.text = "ИТМО Иванов"
        mock_reg = AsyncMock()
        monkeypatch.setattr("main.handle_registration", mock_reg)

        await main.echo(mock_event)
        mock_reg.assert_called_once()

    @pytest.mark.asyncio
    async def test_known_user_student(self, mock_event, monkeypatch):
        """Известный студент — показываем меню отделов."""
        student = {"status": "student", "ВУЗ": "ИТМО"}
        monkeypatch.setattr("main.find_user", lambda uid: student)
        mock_menu = AsyncMock()
        monkeypatch.setattr("main.student.menuSelectDepartment", mock_menu)

        await main.echo(mock_event)
        mock_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_known_user_worker(self, mock_event, monkeypatch):
        """Известный работник — показываем меню работника."""
        worker = {"status": "worker", "ВУЗ": "ИТМО", "Кафедра": "Деканат"}
        monkeypatch.setattr("main.find_user", lambda uid: worker)
        mock_menu = AsyncMock()
        monkeypatch.setattr("main.university.menuSelectWorker", mock_menu)

        await main.echo(mock_event)
        mock_menu.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_user(self, mock_event, monkeypatch):
        """Незнакомый — стартовое меню."""
        monkeypatch.setattr("main.find_user", lambda uid: None)
        mock_menu = AsyncMock()
        monkeypatch.setattr("main.show_start_menu", mock_menu)

        await main.echo(mock_event)
        mock_menu.assert_called_once()