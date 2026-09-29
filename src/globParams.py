class BotState:
    def __init__(self):
        self.registration_open = False
        self.registration_role = None
        # user_id -> {"mode": "answering", "id_query": int}
        # или      {"mode": "asking", ...} для студента
        # или      {"mode": "su"} для суперпользователя
        self.user_sessions = {}

    def start_registration(self, role: str) -> None:
        '''Работа с регистрацией(начинем регистрацию нового пользователя)'''
        self.registration_open = True
        self.registration_role = role

    def stop_registration(self) -> None:
        '''Прекращаем регистрацию открывая канал'''
        self.registration_open = False
        self.registration_role = None

    # --- сессии ---
    def start_answer(self, user_id: int, id_query: int) -> None:
        '''Открываем канал для записи ответа на вопрос'''
        self.user_sessions[user_id] = {"mode": "answering", "id_query": id_query}

    def start_asking(self, user_id: int, id_ask: int, department: str) -> None:
        '''Открываем канал для записи вопроса'''
        self.user_sessions[user_id] = {"mode": "asking", "id_ask": id_ask, "depart": department}

    def get_session(self, user_id: int):
        '''Получаем статус для определённого пользователя'''
        return self.user_sessions.get(user_id)

    def clear_session(self, user_id: int) -> None:
        '''Удаляем статус пользователя если он уже не актуален!!!'''
        self.user_sessions.pop(user_id, None)

    # --- суперпользователь ---
    def enter_su(self, user_id: int) -> None:
        '''Включаем режим суперпользователя'''
        self.user_sessions[user_id] = {"mode": "su"}

    def is_su(self, user_id: int) -> bool:
        '''Проверяем, находится ли пользователь в режиме SU'''
        s = self.user_sessions.get(user_id)
        return s is not None and s.get("mode") == "su"

    def exit_su(self, user_id: int) -> None:
        '''Выключаем режим суперпользователя'''
        s = self.user_sessions.get(user_id)
        if s is not None and s.get("mode") == "su":
            self.user_sessions.pop(user_id, None)


state = BotState()