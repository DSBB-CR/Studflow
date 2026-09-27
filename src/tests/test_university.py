import pytest
from unittest.mock import AsyncMock, MagicMock

import university
from dataBase.query import find_queries_for_worker


@pytest.fixture
def mock_event():
    event = MagicMock()
    event.message = MagicMock()
    event.message.answer = AsyncMock()
    return event


class TestMenuSelectWorker:
    @pytest.mark.asyncio
    async def test_sends_menu(self, mock_event):
        worker = {"Имя": "Пётр"}
        await university.menuSelectWorker(mock_event, worker)
        mock_event.message.answer.assert_called_once()
        call_args = mock_event.message.answer.call_args
        assert "Выберите действие" in call_args.kwargs["text"]
        assert "Пётр" in call_args.kwargs["text"]


class TestShowQueriesForWorker:
    @pytest.mark.asyncio
    async def test_no_queries(self, mock_event):
        worker = {"ВУЗ": "МГУ", "Кафедра": "Деканат"}
        await university.show_queries_for_worker(mock_event, worker)
        call_args = mock_event.message.answer.call_args
        assert "вопросов пока нет" in call_args.kwargs["text"]

    @pytest.mark.asyncio
    async def test_sends_queries(self, mock_event, sample_query):
        worker = {"ВУЗ": "ИТМО", "Кафедра": "Деканат"}
        await university.show_queries_for_worker(mock_event, worker)
        assert mock_event.message.answer.call_count == 1
        call_args = mock_event.message.answer.call_args
        assert "📩 Вопрос №" in call_args.kwargs["text"]