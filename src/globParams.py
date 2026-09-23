class BotState:
    def __init__(self):
        self.registration_open = False
        self.registration_role = None
        # user_id -> {"mode": "answering", "id_query": int}
        # или      {"mode": "asking", ...} для студента (если понадобится)
        self.user_sessions = {}

    def start_registration(self, role: str) -> None:
        self.registration_open = True
        self.registration_role = role

    def stop_registration(self) -> None:
        self.registration_open = False
        self.registration_role = None

    # --- сессии ---
    def start_answer(self, user_id: int, id_query: int) -> None:
        self.user_sessions[user_id] = {"mode": "answering", "id_query": id_query}

    def get_session(self, user_id: int):
        return self.user_sessions.get(user_id)

    def clear_session(self, user_id: int) -> None:
        self.user_sessions.pop(user_id, None)


state = BotState()