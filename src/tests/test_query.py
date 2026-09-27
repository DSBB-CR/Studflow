import pytest
from dataBase.query import (
    next_query_id,
    find_user,
    goToJsonStudent,
    goToJsonWorker,
    find_query_by_id,
    find_queries_for_worker,
    find_queries_for_student,
    save_query,
    save_answer,
)


class TestNextQueryId:
    def test_returns_sequential_ids(self, counters_col):
        assert next_query_id() == 1
        assert next_query_id() == 2
        assert next_query_id() == 3


class TestFindUser:
    def test_returns_none_for_none(self):
        assert find_user(None) is None

    def test_returns_none_for_unknown(self):
        assert find_user(99999999) is None

    def test_returns_student(self, sample_user):
        result = find_user(12345)
        assert result is not None
        assert result["status"] == "student"
        assert result["id"] == 12345
        assert result["ВУЗ"] == "ИТМО"
        assert result["Фамилия"] == "Иванов"
        assert result["Номер группы"] == "P3112"

    def test_returns_worker_as_worker_status(self, sample_worker):
        result = find_user(99999)
        assert result is not None
        assert result["status"] == "worker"  # "staff" → "worker"
        assert result["Кафедра"] == "Деканат"


class TestGoToJsonStudent:
    def test_returns_false_for_wrong_length(self):
        assert goToJsonStudent(["ИТМО", "Иванов"]) is False

    def test_saves_student(self, users_col):
        data = [
            "ИТМО", "Иванов", "Иван", "Иванович",
            "P3112", "Программирование", "2022", "2026", "123456", 12345,
        ]
        assert goToJsonStudent(data) is True
        doc = users_col.find_one({"user_id": 12345})
        assert doc is not None
        assert doc["role"] == "student"
        assert doc["university"] == "ИТМО"

    def test_updates_existing(self, users_col, sample_user):
        data = [
            "МГУ", "Петров", "Пётр", "Петрович",
            "P9999", "Физика", "2020", "2024", "999999", 12345,
        ]
        goToJsonStudent(data)
        doc = users_col.find_one({"user_id": 12345})
        assert doc["university"] == "МГУ"
        assert doc["last_name"] == "Петров"


class TestGoToJsonWorker:
    def test_returns_false_for_wrong_length(self):
        assert goToJsonWorker(["ИТМО", "Петров"]) is False

    def test_saves_worker(self, users_col):
        data = ["ИТМО", "Петров", "Пётр", "", "Деканат", "Специалист", 99999]
        assert goToJsonWorker(data) is True
        doc = users_col.find_one({"user_id": 99999})
        assert doc["role"] == "staff"
        assert doc["staff_profile"]["department"] == "Деканат"


class TestFindQueryById:
    def test_returns_none_for_unknown(self):
        assert find_query_by_id(9999) is None

    def test_returns_query(self, sample_query):
        result = find_query_by_id(1111)
        assert result is not None
        assert result["id_query"] == 1111
        assert result["Вопрос"] == "Который час?"
        assert result["Кафедра"] == "Деканат"
        assert result["status"] == "pending"


class TestFindQueriesForWorker:
    def test_returns_matching_queries(self, sample_query):
        worker = {"ВУЗ": "ИТМО", "Кафедра": "Деканат"}
        result = find_queries_for_worker(worker)
        assert len(result) == 1
        assert result[0]["id_query"] == 1111

    def test_returns_empty_for_unknown_vuz(self, sample_query):
        worker = {"ВУЗ": "МГУ", "Кафедра": "Деканат"}
        result = find_queries_for_worker(worker)
        assert result == []

    def test_returns_empty_for_unknown_department(self, sample_query):
        worker = {"ВУЗ": "ИТМО", "Кафедра": "Физра"}
        result = find_queries_for_worker(worker)
        assert result == []

    def test_does_not_return_answered(self, queries_col, sample_query):
        queries_col.update_one(
            {"query_id": 1111},
            {"$set": {"status": "answered"}},
        )
        worker = {"ВУЗ": "ИТМО", "Кафедра": "Деканат"}
        result = find_queries_for_worker(worker)
        assert result == []


class TestSaveQuery:
    def test_raises_for_unknown_user(self, mock_mongo):
        with pytest.raises(ValueError):
            save_query(2222, 99999999, "Деканат", "Вопрос?")

    def test_saves_query(self, sample_user, queries_col):
        save_query(2222, 12345, "Деканат", "Вопрос?")
        doc = queries_col.find_one({"query_id": 2222})
        assert doc is not None
        assert doc["question"] == "Вопрос?"
        assert doc["department"] == "Деканат"
        assert doc["status"] == "pending"
        assert doc["student"]["full_name"] == "Иванов Иван Иванович"


class TestSaveAnswer:
    def test_saves_answer(self, sample_query, sample_worker, queries_col):
        save_answer(1111, 12345, 99999, "13:00")
        doc = queries_col.find_one({"query_id": 1111})
        assert doc["status"] == "answered"
        assert doc["answer"]["text"] == "13:00"
        assert doc["answer"]["answered_by"] == 99999


class TestFindQueriesForStudent:
    def test_returns_answered_for_student(self, queries_col, sample_query):
        queries_col.update_one(
            {"query_id": 1111},
            {"$set": {
                "status": "answered",
                "answer": {"text": "13:00", "answered_by": 99999},
            }},
        )
        result = find_queries_for_student(12345)
        assert len(result) == 1
        assert result[0]["answer_text"] == "13:00"

    def test_returns_empty_for_unknown(self):
        assert find_queries_for_student(99999999) == []