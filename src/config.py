import os
from pathlib import Path
from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

MAX_TOKEN = os.getenv("MAX_TOKEN")
GIGACHAT_KEY = os.getenv("GIGACHAT_KEY")

UNIVERSITIES = {"СПБГУ", "СПБГТИ(ТУ)", "ЛЭТИ", "ИТМО", "МГУ", "ВШЭ", "МИРЭА", "ГУАП"}

DEPARTMENTS = {"ИТМО": ["Деканат", "Физра", "Отдел кадров", "СА"]}

IN_LOGGIN = {"29602091": "Student", "296020911": "Worker"}
