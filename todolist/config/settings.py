# todolist/config/settings.py
from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    MAX_NUMBER_OF_PROJECT: int = int(os.getenv("MAX_NUMBER_OF_PROJECT", "100"))

settings = Settings()
