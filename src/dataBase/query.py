import json

dataBaseDEMO = []


def goToJsonStudent(studInfo) -> bool:
    """
    Ожидает список из 10 элементов:
    [ВУЗ, Фамилия, Имя, Отчество, Группа, Направление,
     Год поступления, Год выпуска, Номер студенческого, user_id]
    """
    if len(studInfo) != 10:
        return False

    user_data = {
        "status": "student",
        "id": studInfo[-1],
        "ВУЗ": studInfo[0],
        "Фамилия": studInfo[1],
        "Имя": studInfo[2],
        "Отчество": studInfo[3],
        "Номер группы": studInfo[4],
        "Направление": studInfo[5],
        "Год поступления": studInfo[6],
        "Год выпуска": studInfo[7],
        "Номер студенческого": studInfo[8],
    }

    print(json.dumps(user_data, ensure_ascii=False))
    dataBaseDEMO.append(user_data)
    return True


def goToJsonWorker(workInfo) -> bool:
    """
    Ожидает список из 7 элементов:
    [ВУЗ, Фамилия, Имя, Отчество, Кафедра, Должность, user_id]
    """
    if len(workInfo) != 7:
        return False

    worker_data = {
        "status": "worker",
        "id": workInfo[-1],
        "ВУЗ": workInfo[0],
        "Фамилия": workInfo[1],
        "Имя": workInfo[2],
        "Отчество": workInfo[3],
        "Кафедра": workInfo[4],
        "Должность": workInfo[5],
    }

    print(json.dumps(worker_data, ensure_ascii=False))
    dataBaseDEMO.append(worker_data)
    return True


def find_user(user_id):
    """Возвращает запись пользователя или None."""
    for user in dataBaseDEMO:
        if str(user["id"]) == str(user_id):
            return user
    return None