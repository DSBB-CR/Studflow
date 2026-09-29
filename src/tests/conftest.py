import sys
from unittest.mock import MagicMock

# Мокаем Bot ДО импорта main
import maxapi
maxapi.Bot = MagicMock(return_value=MagicMock())

# Дальше — обычные фикстуры
import pytest
import mongomock
from dataBase import mongo_client

@pytest.fixture(autouse=True)
def mock_mongo(monkeypatch):
    from dataBase import query  # ← импортируем query
    
    mock_client = mongomock.MongoClient()
    mock_db = mock_client["studflow_test"]
    
    # Подменяем коллекции В query.py
    monkeypatch.setattr(query, "users_col", mock_db["users"])
    monkeypatch.setattr(query, "queries_col", mock_db["queries"])
    monkeypatch.setattr(query, "counters_col", mock_db["counters"])
    monkeypatch.setattr(query, "universities_col", mock_db["universities"])
    
    yield mock_db
    
    mock_client.drop_database("studflow_test")


@pytest.fixture
def users_col(mock_mongo):
    return mock_mongo["users"]


@pytest.fixture
def queries_col(mock_mongo):
    return mock_mongo["queries"]


@pytest.fixture
def counters_col(mock_mongo):
    return mock_mongo["counters"]


@pytest.fixture
def sample_user(users_col):
    """Готовый студент в БД."""
    doc = {
        "user_id": 12345,
        "chat_id": 12345,
        "role": "student",
        "last_name": "Иванов",
        "first_name": "Иван",
        "patronymic": "Иванович",
        "university": "ИТМО",
        "student_profile": {
            "group": "P3112",
            "direction": "Программирование",
            "admission_year": 2022,
            "graduation_year": 2026,
            "student_number": "123456",
        },
        "staff_profile": None,
    }
    users_col.insert_one(doc)
    return doc


@pytest.fixture
def sample_worker(users_col):
    """Готовый работник в БД."""
    doc = {
        "user_id": 99999,
        "chat_id": 99999,
        "role": "staff",
        "last_name": "Петров",
        "first_name": "Пётр",
        "patronymic": "",
        "university": "ИТМО",
        "student_profile": None,
        "staff_profile": {
            "department": "Деканат",
            "position": "Специалист",
        },
    }
    users_col.insert_one(doc)
    return doc


@pytest.fixture
def sample_query(queries_col):
    """Готовый вопрос в БД."""
    doc = {
        "query_id": 1111,
        "student": {
            "user_id": 12345,
            "chat_id": 12345,
            "full_name": "Иванов Иван Иванович",
            "university": "ИТМО",
        },
        "department": "Деканат",
        "question": "Который час?",
        "status": "pending",
        "answer": None,
    }
    queries_col.insert_one(doc)
    return doc

@pytest.fixture(autouse=True)
def reset_state():
    """Сбрасывает состояние бота перед каждым тестом."""
    from globParams import state
    state.user_sessions = {}
    state.registration_open = False
    state.registration_role = None
    yield
    state.user_sessions = {}
    state.registration_open = False
    state.registration_role = None