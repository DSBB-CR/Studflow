import os
from dotenv import load_dotenv
from dataBase.query import find_user, dataBaseDEMO

load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")
GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")

UNIVERSITIES = {
    "СПБГУ",
    "СПБГТИ(ТУ)",
    "ЛЭТИ",
    "ИТМО",
    "МГУ",
    "ВШЭ",
    "МИРЭА",
    "ГУАП",
}

DEPARTMENTS = {
    "ИТМО": ["Деканат", "Физра", "Отдел кадров"],
}

IN_LOGGIN = {
    "29602091": "Student",
    "296020911": "Worker",
}

QUERY_STUDENTS = [
    {
        "id_query" : 1111,
        "Студент" : "Петр Петрович sdsdsds",
        "id_stud" : 29602091,
        "ВУЗ" : "ИТМО",
        "Кафедра" : "а",
        "Вопрос" : "Здравствуйте который час?"
    },
    {
        "id_query" : 2222,
        "Студент" : "Никита Опатыч",
        "id_stud" : 29602091,
        "ВУЗ" : "ИТМО",
        "Кафедра" : "а",
        "Вопрос" : "Здравствуйте который час и когда кушать?"
    }
]

ANSWER_WORKERS = [
    {
        "id_query" : 2222,
        "id_stud" : 29602091,
        "id_worker" : 29602091,
        "response" : "привет кушать в 13:00",
    },
    {
        "id_query" : 1111,
        "id_stud" : 29602091,
        "id_worker" : 29602091,
        "response" : "привет кушать в 13:00",
    },
]


def find_queries_for_worker(worker: dict) -> list:
    """Возвращает вопросы, адресованные кафедре работника в его ВУЗе."""
    return [
        q for q in QUERY_STUDENTS
        if q["ВУЗ"] == worker["ВУЗ"].upper() and q["Кафедра"] == str(worker["Кафедра"]).lower()
    ]


def find_query_by_id(id_query: int):
    for q in QUERY_STUDENTS:
        if q["id_query"] == id_query:
            return q
    return None


def save_answer(id_query: int, id_stud: int, id_worker: int, response: str) -> None:
    ANSWER_WORKERS.append({
        "id_query": id_query,
        "id_stud": id_stud,
        "id_worker": id_worker,
        "response": response,
    })

def save_query(id_query: int, id_stud: int, department: str, query: str ) -> None:
    stud = find_user(id_stud)
    QUERY_STUDENTS.append({
        "id_query" : id_query,
        "id_stud" : id_stud,
        "Кафедра" : department,
        "Вопрос": query,
        "ВУЗ" : stud['ВУЗ'],
        "Студент" : stud["Фамилия"] + " " + stud["Имя"] + " " + stud["Отчество"]
    })
            

def print_query() -> None:
    for i in QUERY_STUDENTS:
        print(i)

