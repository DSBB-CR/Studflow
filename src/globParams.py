class BotState:
    def __init__(self):
        self.registration_open = False
        self.registration_role = None  # "student" | "worker" | None

    def start_registration(self, role: str) -> None:
        self.registration_open = True
        self.registration_role = role

    def stop_registration(self) -> None:
        self.registration_open = False
        self.registration_role = None


state = BotState()