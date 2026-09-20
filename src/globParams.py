
class Registration():
    def __init__(self):
        self.is_reg = False

    def __call__(self):
        self.is_reg = not self.is_reg

    def get_status(self) -> bool:
        return self.is_reg

registation = Registration()