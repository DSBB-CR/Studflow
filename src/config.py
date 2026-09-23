import os
from dotenv import load_dotenv

load_dotenv()

MAX_TOKEN = os.getenv("MAX_TOKEN")
GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")

UNIVERSITIES = {
    "СПБГТУ",
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
        "Студент" : "Петр Петрович",
        "ВУЗ" : "ИТМО",
        "Кафедра" : "а",
        "Вопрос" : "Здравствуйте который час?"
    },
    {
        "Студент" : "Никита Опатыч",
        "ВУЗ" : "ИТМО",
        "Кафедра" : "а",
        "Вопрос" : "Здравствуйте который час и когда кушать?"
    }
]