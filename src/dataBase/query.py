import json

dataBaseDEMO = []

def goToJson(studInfo) -> None:
    if len(studInfo) == 10:
        user_data  = {
            "id" : studInfo[-1],
            "ВУЗ": studInfo[0],
            "Фамилия" : studInfo[1],
            "Имя" : studInfo[2],
            "Отчество" : studInfo[3],
            "Номер группы" : studInfo[4],
            "Направление" : studInfo[5],
            "Год поступления" : studInfo[6],
            "Год выпуска" : studInfo[7],
            "Номер студенческого" : studInfo[8],
        }
        json_string = json.dumps(user_data, ensure_ascii=False)
        print(json_string)
        dataBaseDEMO.append(user_data)
        


