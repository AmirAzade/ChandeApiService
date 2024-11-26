import datetime

class Token:
    def __init__(self, value: str, life_span: int = 600, generated_at: datetime.datetime = datetime.datetime.now()):
        self.life_span = life_span
        self.generated_at = generated_at
        self.value = value

    def is_expired(self) -> bool:
        return datetime.datetime.now() - self.generated_at > datetime.timedelta(seconds=self.life_span)