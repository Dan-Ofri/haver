"""Red-flag safety: checked in code before the model sees a question.

If a question describes a red flag, the answer is a fixed message that tells the user to stop and
get medical help. The model is not called, so it cannot talk the user into exercising anyway.
Plugins supply the flags for their domain. Matching errs on the side of caution.
"""

import re
from dataclasses import dataclass

from pydantic import BaseModel

HEBREW = re.compile(r"[֐-׿]")


@dataclass(frozen=True)
class RedFlag:
    id: str
    patterns: tuple[str, ...]
    message: str
    message_he: str


class SafetyAlert(BaseModel):
    flag_id: str
    message: str


def check(question: str, flags: list[RedFlag]) -> SafetyAlert | None:
    """The first flag whose pattern appears in the question, or None."""
    for flag in flags:
        if any(re.search(p, question, re.IGNORECASE) for p in flag.patterns):
            hebrew = HEBREW.search(question) is not None
            return SafetyAlert(flag_id=flag.id, message=flag.message_he if hebrew else flag.message)
    return None
