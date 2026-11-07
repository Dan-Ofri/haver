"""Warning signs in a training context. A match means: stop, see a doctor, no exercises."""

from haver.core.safety import RedFlag

EMERGENCY = RedFlag(
    id="emergency",
    patterns=(
        r"chest\s+(pain|pressure|tightness|discomfort)",
        r"(pain|pressure|tightness)\s+(in|across)\s+(my\s+)?chest",
        r"\b(faint(ed|ing)?|passed\s+out|blacked\s+out|blackout)\b",
        r"(can'?t|cannot|hard\s+to|trouble|difficulty)\s+breath",
        r"short(ness)?\s+of\s+breath",
        r"(sudden|worst|severe|thunderclap).{0,20}headache",
        r"slurred\s+speech|face\s+(is\s+)?droop",
        r"(lost|loss\s+of|lose|losing|can'?t\s+control).{0,20}(bladder|bowel)",
        r"(numb|numbness).{0,30}(groin|genital|saddle|between\s+(my\s+)?legs|inner\s+thigh)",
        r"כאב(ים)?\s+(חזק\s+)?בחזה|לחץ\s+בחזה|צריבה\s+בחזה",
        r"התעלפ|עילפון",
        r"קשה\s+(לי\s+)?לנשום|קוצר\s+נשימה|לא\s+מצליח\s+לנשום",
        r"כאב\s+ראש\s+(פתאומי|חזק\s+מאוד|הכי\s+חזק)",
        r"שליטה\s+(ב)?(שתן|צרכים|סוגרים)",
        r"(נימול|חוסר\s+תחושה).{0,30}(מפשעה|בין\s+הרגליים|ירכיים\s+פנימיות)",
    ),
    message=(
        "Please stop exercising now. What you describe can be a sign of a serious problem, and I "
        "can't judge that. Contact a doctor today. If it is severe, sudden or not passing, call "
        "your local emergency number or go to the emergency room. I won't suggest exercises until "
        "a doctor has checked you."
    ),
    message_he=(
        "בבקשה עצור את האימון עכשיו. מה שאתה מתאר יכול להעיד על בעיה רצינית, ואני לא יכול לשפוט "
        "את זה. פנה לרופא היום. אם זה חזק, פתאומי או לא עובר, התקשר למספר החירום או לך למיון. "
        "לא אציע תרגילים עד שרופא יבדוק אותך."
    ),
)

NERVE = RedFlag(
    id="nerve",
    patterns=(
        r"\b(numb|numbness|tingling|pins\s+and\s+needles|weakness)\b.{0,40}"
        r"\b(leg|legs|arm|arms|foot|feet|hand|hands)\b",
        r"\b(leg|legs|arm|arms|foot|feet|hand|hands)\b.{0,40}"
        r"\b(numb|numbness|tingling|went\s+weak|is\s+weak|are\s+weak|asleep)\b",
        r"(pain|ache)\s+(that\s+)?(shoots|radiates|spreads|goes|runs)\s+(down|into|to)\b",
        r"radiating\s+pain|pain\s+radiat",
        r"נימול|נימלה|נימלו|חוסר\s+תחושה|ירידה\s+בתחושה|עקצוץ|מקרינ|קורן\s+ל",
        r"(רגל|יד).{0,15}נרדמ",
        r"חולשה\s+ב(רגל|יד)",
    ),
    message=(
        "Please stop training the affected area and see a doctor soon. Numbness, tingling, "
        "weakness or pain that spreads down a limb can mean a nerve is involved, and I can't "
        "judge that. I won't suggest exercises for this. If you also lose control of your bladder "
        "or bowels, or feel numb between your legs, go to the emergency room now."
    ),
    message_he=(
        "בבקשה הפסק לאמן את האזור הפגוע ופנה לרופא בקרוב. נימול, עקצוץ, חולשה או כאב שמקרין "
        "לגפה יכולים להעיד על מעורבות של עצב, ואני לא יכול לשפוט את זה. לא אציע תרגילים למצב "
        "הזה. אם יש גם אובדן שליטה בשתן או בצרכים, או נימול בין הרגליים, לך למיון מיד."
    ),
)

CRISIS = RedFlag(
    id="crisis",
    patterns=(
        r"(kill|hurt|harm)\s+myself",
        r"want\s+to\s+die|end\s+my\s+life|suicid",
        r"להתאבד|אובדני|לפגוע\s+בעצמי|רוצה\s+למות|לא\s+רוצה\s+לחיות",
    ),
    message=(
        "I'm sorry you're feeling this way. I'm a training coach and can't help with this, but "
        "you don't have to face it alone. Please contact your local emergency number or a crisis "
        "line now, or reach out to someone close to you."
    ),
    message_he=(
        "אני מצטער שאתה מרגיש ככה. אני מאמן אימונים ולא יכול לעזור בזה, אבל אתה לא צריך להתמודד "
        "לבד. בבקשה פנה עכשיו למספר החירום או לקו סיוע, או לאדם קרוב אליך."
    ),
)

RED_FLAGS = [CRISIS, EMERGENCY, NERVE]
