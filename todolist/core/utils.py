# todolist/core/utils.py
def word_count(s: str | None) -> int:
    if not s: return 0
    return len([w for w in s.split() if w.strip()])
