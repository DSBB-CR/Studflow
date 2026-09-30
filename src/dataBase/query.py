import json
from datetime import datetime
from dataBase.mongo_client import (
    users_col,
    universities_col,
    counters_col,
    queries_col,
)


# ============================================================
# Счётчик query_id (короткие числовые id обращений)
# ============================================================

def next_query_id() -> int:
    doc = counters_col.find_one_and_update(
        {"_id": "query_id"},
        {"$inc": {"seq": 1}},
        return_document=True,   # pymongo.ReturnDocument.AFTER
        upsert=True,
    )
    return int(doc["seq"])


# ============================================================
# Пользователи
# ============================================================

def find_user(user_id) -> dict | None:
    """
    Возвращает запись пользователя в формате, ожидаемом ботом:
    {
      "status": "student"|"worker",
      "id": <user_id>,
      "ВУЗ": ...,
      "Фамилия": ..., "Имя": ..., "Отчество": ...,
      # для студента:
      "Номер группы", "Направление", "Год поступления",
      "Год выпуска", "Номер студенческого",
      # для работника:
      "Кафедра", "Должность",
    }
    или None, если не найден.
    """
    if user_id is None:
        return None

    doc = users_col.find_one({"user_id": int(user_id)})
    if not doc:
        return None

    out = {
        "status": doc["role"],          
        "id": doc["user_id"],
        "ВУЗ": doc["university"],
        "Фамилия": doc.get("last_name", ""),
        "Имя": doc.get("first_name", ""),
        "Отчество": doc.get("patronymic") or "",
    }

    
    if out["status"] == "staff":
        out["status"] = "worker"

    sp = doc.get("student_profile") or {}
    if sp:
        out["Номер группы"]     = sp.get("group", "")
        out["Направление"]      = sp.get("direction", "")
        out["Год поступления"]  = sp.get("admission_year", "")
        out["Год выпуска"]      = sp.get("graduation_year", "")
        out["Номер студенческого"] = sp.get("student_number", "")

    stp = doc.get("staff_profile") or {}
    if stp:
        out["Кафедра"]   = stp.get("department", "")
        out["Должность"] = stp.get("position", "")

    return out


def _split_fio(fio: str):
    """Разбивает ФИО 'Иванов Иван Иванович' на три части."""
    parts = fio.split(maxsplit=2)
    while len(parts) < 3:
        parts.append("")
    return parts[0], parts[1], parts[2]


def goToJsonStudent(studInfo) -> bool:
    """
    Ожидает список из 10 элементов:
    [ВУЗ, Фамилия, Имя, Отчество, Группа, Направление,
     Год поступления, Год выпуска, Номер студенческого, user_id]
    Сохраняет в коллекцию users.
    """
    if len(studInfo) != 10:
        return False

    (uni, last_name, first_name, patronymic,
     group, direction, admission_year, graduation_year,
     student_number, user_id) = studInfo

    doc = {
        "chat_id": int(user_id),      # упрощение: chat_id == user_id
        "user_id": int(user_id),
        "role": "student",
        "last_name": last_name,
        "first_name": first_name,
        "patronymic": patronymic,
        "university": uni,
        "student_profile": {
            "group": group,
            "direction": direction,
            "admission_year": int(admission_year) if str(admission_year).isdigit() else None,
            "graduation_year": int(graduation_year) if str(graduation_year).isdigit() else None,
            "student_number": student_number,
        },
        "staff_profile": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    users_col.update_one(
        {"user_id": int(user_id)},
        {"$set": doc},
        upsert=True,
    )
    return True


def goToJsonWorker(workInfo) -> bool:
    """
    Ожидает список из 7 элементов:
    [ВУЗ, Фамилия, Имя, Отчество, Кафедра, Должность, user_id]
    Сохраняет в коллекцию users.
    """
    if len(workInfo) != 7:
        return False

    (uni, last_name, first_name, patronymic,
     department, position, user_id) = workInfo

    doc = {
        "chat_id": int(user_id),
        "user_id": int(user_id),
        "role": "staff",              # в Mongo-схеме роль называется "staff"
        "last_name": last_name,
        "first_name": first_name,
        "patronymic": patronymic,
        "university": uni,
        "student_profile": None,
        "staff_profile": {
            "department": department,
            "position": position,
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    users_col.update_one(
        {"user_id": int(user_id)},
        {"$set": doc},
        upsert=True,
    )
    return True


# ============================================================
# Обращения (queries)
# ============================================================

def _query_to_bot_format(doc: dict) -> dict:
    """Приводит документ queries к формату, который ждёт бот."""
    ans = doc.get("answer") or {}
    return {
        "id_query": doc["query_id"],
        "id_stud": doc["student"]["user_id"],
        "Студент": doc["student"].get("full_name", ""),
        "ВУЗ": doc["student"].get("university", ""),
        "Кафедра": doc.get("department", ""),
        "Вопрос": doc.get("question", ""),
        # для совместимости с student.py / answer-view
        "status": doc.get("status", "pending"),
        "answer_text": ans.get("text"),
        "answered_by": ans.get("answered_by"),
        "answered_by_name": ans.get("answered_by_name"),
        "answered_at": ans.get("answered_at"),
    }


def find_query_by_id(id_query: int) -> dict | None:
    doc = queries_col.find_one({"query_id": int(id_query)})
    return _query_to_bot_format(doc) if doc else None


def find_queries_for_worker(worker: dict) -> list:
    """
    Возвращает вопросы, адресованные кафедре работника в его ВУЗе
    и ещё не отвеченные.
    """
    uni = str(worker["ВУЗ"]).upper()
    dep = str(worker["Кафедра"]).strip()

    cursor = queries_col.find({
        "student.university": uni,
        "department": dep,
        "status": "pending",
    })
    return [_query_to_bot_format(d) for d in cursor]


def find_queries_for_student(user_id: int) -> list:
    """Ответы на вопросы конкретного студента (для кнопки «Мои ответы»)."""
    cursor = queries_col.find({
        "student.user_id": int(user_id),
        "status": "answered",
    })
    return [_query_to_bot_format(d) for d in cursor]


# ============================================================
# SU: информация о вузах
# ============================================================

def get_universities_info() -> str:
    """Возвращает список ВУЗов с количеством студентов и работников."""
    pipeline = [
        {
            "$group": {
                "_id": "$university",
                "total": {"$sum": 1},
                "students": {
                    "$sum": {"$cond": [{"$eq": ["$status", "student"]}, 1, 0]}
                },
                "workers": {
                    "$sum": {"$cond": [{"$eq": ["$status", "worker"]}, 1, 0]}
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]

    rows = list(users_col.aggregate(pipeline))
    if not rows:
        return "Пока нет зарегистрированных пользователей."

    lines = []
    for r in rows:
        uni = r["_id"] or "(без ВУЗа)"
        lines.append(
            f"• {uni}: всего {r['total']} "
            f"(студентов {r['students']}, работников {r['workers']})"
        )
    return "\n".join(lines)


# ============================================================
# SU: информация о студентах
# ============================================================

def get_students_info(limit: int = 30) -> str:
    """Список студентов: ФИО, ВУЗ, кафедра."""
    cursor = users_col.find({"status": "student"}).limit(limit)
    rows = list(cursor)
    if not rows:
        return "Студентов в БД нет."

    lines = []
    for s in rows:
        fio = " ".join(filter(None, [
            s.get("last_name", ""),
            s.get("first_name", ""),
            s.get("patronymic", ""),
        ])) or "(без имени)"
        uni = s.get("university", "") or "—"
        dep = s.get("department", "") or "—"
        uid = s.get("user_id", "?")
        lines.append(f"• {fio} | {uni} | {dep} | id={uid}")

    total = users_col.count_documents({"status": "student"})
    header = f"Студентов всего: {total}. Показаны первые {len(rows)}:\n"
    return header + "\n".join(lines)


# ============================================================
# SU: дамп вопросов из БД
# ============================================================

def dump_queries(limit: int = 20) -> str:
    """Последние вопросы с кратким статусом."""
    cursor = (
        queries_col.find()
        .sort("created_at", -1)
        .limit(limit)
    )
    rows = list(cursor)
    if not rows:
        return "Обращений в БД нет."

    lines = []
    for d in rows:
        f = _query_to_bot_format(d)
        status = f["status"]
        mark = "✅" if status == "answered" else "⏳"
        q = (f["Вопрос"] or "")[:80]
        lines.append(
            f"{mark} #{f['id_query']} | {f['Студент'] or '—'} | "
            f"{f['Кафедра'] or '—'} | {q}"
        )

    total = queries_col.count_documents({})
    header = f"Всего обращений: {total}. Последние {len(rows)}:\n"
    return header + "\n".join(lines)


def save_query(id_query: int, id_stud: int, department: str, query: str) -> None:
    """Создаёт новое обращение студента."""
    student = users_col.find_one({"user_id": int(id_stud)})
    if student is None:
        raise ValueError(f"Пользователь {id_stud} не найден в users")

    full_name = " ".join(filter(None, [
        student.get("last_name", ""),
        student.get("first_name", ""),
        student.get("patronymic", ""),
    ]))

    queries_col.insert_one({
        "query_id": int(id_query),
        "student": {
            "user_id": int(id_stud),
            "chat_id": int(student.get("chat_id", id_stud)),
            "full_name": full_name,
            "university": student.get("university", ""),
        },
        "department": department,
        "question": query,
        "status": "pending",
        "answer": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })


def save_answer(id_query: int, id_stud: int, id_worker: int, response: str) -> None:
    """Записывает ответ работника внутрь документа query."""
    worker = users_col.find_one({"user_id": int(id_worker)})
    worker_name = ""
    if worker:
        worker_name = " ".join(filter(None, [
            worker.get("last_name", ""),
            worker.get("first_name", ""),
        ]))

    queries_col.update_one(
        {"query_id": int(id_query)},
        {"$set": {
            "status": "answered",
            "answer": {
                "text": response,
                "answered_by": int(id_worker),
                "answered_by_name": worker_name,
                "answered_at": datetime.utcnow(),
            },
            "updated_at": datetime.utcnow(),
        }},
    )
# ============================================================
# Удаление студента (без затрагивания связанных данных)
# ============================================================

def delete_user(user_id: int) -> None:
    """Удаляет профиль из коллекции users.
    Связанные данные (обращения в queries и т.п.) не трогает."""
    if user_id is None:
        return
    users_col.delete_one({"user_id": int(user_id)})


def delete_user_by_chat_id(chat_id: int) -> None:
    """То же самое, но поиск по chat_id."""
    if chat_id is None:
        return
    doc = users_col.find_one({"chat_id": int(chat_id)})
    if doc:
        users_col.delete_one({"_id": doc["_id"]})

# ============================================================
# Утилита для отладки (аналог print_query)
# ============================================================

def print_query() -> None:
    for d in queries_col.find():
        print(_query_to_bot_format(d))
