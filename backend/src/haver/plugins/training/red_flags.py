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
        r"\b(chest|heart)\b.{0,30}\b(hurt|hurts|hurting|tight|squeez\w*|crush\w*)",
        r"\b(hurt|hurts|hurting|tight|squeez\w*|crush\w*)\b.{0,30}\bchest\b",
        r"\b(left\s+arm|jaw)\b.{0,25}\b(pain|hurt|hurts|ache)|(pain|hurt|hurts|ache)\b.{0,25}\b(left\s+arm|jaw)",
        r"heart\s+(is\s+)?(racing|pounding|fluttering|skipping)|palpitation|irregular\s+heart|racing\s+heart",
        r"\b(dizzy|dizziness|lightheaded|light-headed)\b",
        r"(couldn'?t|can'?t|cannot|unable\s+to|struggl\w+\s+to|hard\s+to|trouble|difficulty)\s+(to\s+)?(catch\s+my\s+)?breath",
        r"\bgasping\b|lost\s+consciousness|\bI\s+(just\s+)?collapsed\b",
        r"(cough\w*|spit\w*|vomit\w*)\s+(up\s+)?blood|blood\s+in\s+(my\s+)?(urine|stool)",
        r"(blurr?y|double)\s+vision|vision\s+(went|is|got)\s+(blurr?y|dark)|lost\s+(my\s+)?vision",
        r"(peed|wet|soiled)\s+myself",
        r"incontinen",
        r"(can'?t|cannot|unable\s+to)\s+(feel|control|hold).{0,25}(pee|urin|bladder|bowel|stool|poop)",
        r"slurr|(speech|talking).{0,15}confus|face\s+(is\s+)?(numb|droop)|sudden\s+(weakness|confusion)",
        r"כואב\s+(לי\s+)?(ב)?חזה|כאב\s+ב(זרוע|לסת)",
        r"דופק\s+(מהיר|לא\s+סדיר)|פלפיטציות|לב\s+(דופק|מתפרע)",
        r"סחרחורת|מסוחרר",
        r"איבדתי\s+(את\s+)?הכרה|איבוד\s+הכרה|נחנקתי|ניסיתי\s+לנשום",
        r"שיעלתי\s+דם|הקאתי\s+דם|דם\s+בשתן",
        r"ראי{1,2}ה\s+(מטושטשת|כפולה)",
        r"כאב(ים)?\s+(חזק\s+)?בחזה|לחץ\s+בחזה|צריבה\s+בחזה",
        r"התעלפ|עילפון",
        r"קשה\s+(לי\s+)?לנשום|קוצר\s+נשימה|לא\s+מצליח\s+לנשום",
        r"כאב\s+ראש\s+(פתאומי|חזק\s+מאוד|הכי\s+חזק)",
        r"שליטה\s+(ב|על\s+ה?)?(שתן|צרכים|סוגרים|צואה)",
        r"דיבור.{0,15}(מבולבל|משובש|מטושטש)|פנים.{0,20}(נשמט|נופל|מעוות)|חולשה\s+פתאומית",
        r"קרסתי",
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
        r"\b(leg|legs|arm|arms|foot|feet|toe|toes|hand|hands|finger|fingers)\b",
        r"\b(leg|legs|arm|arms|foot|feet|toe|toes|hand|hands|finger|fingers)\b.{0,40}"
        r"\b(numb|numbness|tingling|tingly|went\s+weak|is\s+weak|are\s+weak|asleep|gave\s+out)\b",
        r"\b(numb|tingly)\s+(toes|fingers|feet|hands)",
        r"can'?t\s+(feel|move)\s+(my\s+)?(\w+\s+)?(leg|legs|arm|arms|foot|feet|toe|toes|hand|hands|fingers?)",
        r"(pain|ache)\s+(is\s+)?(going|shooting|traveling|travelling|spreading)\s+(down|into|to)\b",
        r"(shoot\w*|radiat\w*|spread\w*|runs?|going)\b.{0,25}\bdown\b.{0,20}\b(leg|arm|foot|hand)",
        r"\bshoots?\s+down|shooting\s+down",
        r"(pain|ache)\s+(that\s+)?(shoots|radiates|spreads|goes|runs)\s+(down|into|to)\b",
        r"radiating\s+pain|pain\s+radiat",
        r"נימול|נימלה|נימלו|חוסר\s+תחושה|ירידה\s+בתחושה|עקצוץ|מקרינ|קורן\s+ל",
        r"(רגל|יד).{0,15}נרדמ",
        r"מרגיש(ה)?\s+את\s+ה(רגל|יד|אצבעות|בהונות)|(רגל|יד|אצבע).{0,12}(קהה|מורדמת)|קהות|דקירות",
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
        r"(kill|hurt|harm|hurting|harming|cut|cutting)\s+myself",
        r"(end|ending|take|taking)\s+my\s+(own\s+)?life",
        r"want\s+to\s+die|end\s+my\s+life|suicid",
        r"don'?t\s+want\s+to\s+(be\s+alive|live|be\s+here)|(end|ending)\s+it\s+all",
        r"thoughts?\s+of\s+(hurting|harming|killing)\s+myself|take\s+my\s+own\s+life",
        r"better\s+off\s+without\s+me",
        r"התאבד|אובדנ|לפגוע\s+בעצמי|פוגע(ת)?\s+בעצמי|למות|לא\s+רוצה\s+(לחיות|להיות\s+כאן)|לסיים\s+את\s+הכל",
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
