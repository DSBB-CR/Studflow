import pytest
from unittest.mock import AsyncMock, MagicMock

import student
from dataBase.query import save_query, save_answer


@pytest.fixture
def mock_event():
    event = MagicMock()
    event.message = MagicMock()
    event.message.answer = AsyncMock()
    return event


@pytest.fixture
def student_user():
    return {"id": 12345, "status": "student", "Имя": "Иван"}


class TestMenuSelectDepartment:
    @pytest.mark.asyncio
    async def test_sends_message_with_departments(self, mock_event):
        uni = {"ВУЗ": "ИТМО"}
        await student.menuSelectDepartment(mock_event, uni)
        mock_event.message.answer.assert_called_once()
        call_args = mock_event.message.answer.call_args
        assert "Выберите кафедру" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_sends_message_when_no_departments(self, mock_event):
        uni = {"ВУЗ": "МГУ"}
        await student.menuSelectDepartment(mock_event, uni)
        call_args = mock_event.message.answer.call_args
        assert "список кафедр не задан" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_keyboard_rows_count(self, mock_event):
        from config import DEPARTMENTS
        uni = {"ВУЗ": "ИТМО"}
        await student.menuSelectDepartment(mock_event, uni)
        call_args = mock_event.message.answer.call_args
        keyboard = call_args.kwargs["attachments"][0]
        expected = len(DEPARTMENTS["ИТМО"]) + 1
        assert len(keyboard.payload.buttons) == expected


class TestShowAnswersForStudent:
    @pytest.mark.asyncio
    async def test_no_answers(self, mock_event, student_user):
        await student.show_answers_for_student(mock_event, student_user)
        call_args = mock_event.message.answer.call_args
        assert "Ответов на ваши вопросы пока нет" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_sends_answers(self, mock_event, sample_query, queries_col):
        queries_col.update_one(
            {"query_id": 1111},
            {"$set": {
                "status": "answered",
                "answer": {
                    "text": "13:00",
                    "answered_by": 99999,
                    "answered_by_name": "Петров Пётр",
                },
            }},
        )
        student_user = {"id": 12345}
        await student.show_answers_for_student(mock_event, student_user)
        assert mock_event.message.answer.call_count == 1