import re
from typing import Dict, List, Tuple

from chatbot.extractors import extract_course_id, extract_simulation_plans


def _normalize_ar(text: str) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    t = t.replace("ـ", "")
    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ة", "ه")
    t = t.replace("ى", "ي")
    t = re.sub(r"[^\w\s\+\-\=]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _contains_any(t: str, phrases: List[str]) -> List[str]:
    hits = []
    for p in phrases:
        if p in t:
            hits.append(p)
    return hits


KW = {
    "knowledge_base_query": {
        "ar": [
            "ما هو تعريف", "ما معنى", "المقصود", "تعريف", "تعريفات",
            "لائحه", "اللائحه", "لائحة", "اللائحة",
            "نظام", "الانظمه", "الأنظمة", "سياسه", "سياسة",
            "حقوق", "حقوق الطلبه", "حقوق الطلبة",
            "تظلم", "تظلمي", "تظلمات",
            "عقوبه", "عقوبة", "عقوبات",
            "لجنه", "لجنة", "اللجنه", "اللجنة",
            "الفصل الصيفي", "فصل صيفي",
            "اختصاصات", "شروط", "ضوابط", "احكام", "أحكام",
            "متى يحق", "هل يحق", "يجوز", "لا يجوز"
                    "ما هو تعريف", "ما معنى", "ما المقصود", "ما المقصود ب",
            "تعريف", "تعريفات",
            "لائحه", "اللائحه", "لائحة", "اللائحة",
            "نظام", "الانظمه", "الأنظمة", "سياسه", "سياسة",
            "حقوق", "حقوق الطلبه", "حقوق الطلبة",
            "تظلم", "تظلمي", "تظلمات",
            "عقوبه", "عقوبة", "عقوبات",
            "لجنه", "لجنة", "اللجنه", "اللجنة",
            "الفصل الصيفي", "فصل صيفي",
            "اختصاصات", "شروط", "ضوابط", "احكام", "أحكام",
            "متى يحق", "هل يحق", "يجوز", "لا يجوز",
            "العام الدراسي", "المستوى الدراسي", "النظام الدراسي", "الدراسي"
        ],
        "en": [
            "definition", "what is the meaning", "what is", "regulation", "policy",
            "rules", "rights", "students rights", "complaint", "appeal",
            "committee", "penalty", "disciplinary", "summer semester",
            "conditions", "requirements", "article", "chapter",
            "academic level",
        "academic year", "study system"
        ],
    },
    "recommendations": {
        "ar": [
            "اقترح", "اقترح لي", "اقتراح", "اقتراحات", "رشح", "رشح لي",
            "وش اسجل", "وش اسجل الفصل", "ايش اسجل", "ايش اخذ", "وش اخذ",
            "ماذا اسجل", "ماذا اخذ", "مواد الفصل", "مواد الفصل القادم",
            "خطه الفصل", "خطة الفصل", "جدول الفصل", "جدولي",
            "افضل مواد", "افضل مقررات", "انسب مواد", "انسب مقررات",
            "مواد مناسبه", "مقررات مناسبه", "مقررات مقترحه", "مواد مقترحه",
            "ابدأ بايش", "اي ماده ابدا", "اي مقرر ابدا",
            "ساعدني اختار مواد", "ساعدني في التسجيل",
            "نصيحه تسجيل", "نصايح تسجيل",
            "وش المواد المناسبه", "وش المواد المناسبة",
            "المواد المناسبه", "المواد المناسبة",
            "الفصل الجاي", "الفصل الجاي؟",
            "مواد مناسبة", "مواد مناسبه",
            "ايش المواد المناسبة", "ايش المواد المناسبه",
            "وش اخذ الفصل الجاي", "وش اسجل الفصل الجاي",
            "مواد الفصل الجاي", "مقررات الفصل الجاي"
        ],
        "en": [
            "recommend", "recommend me", "suggest", "suggest me", "suggestion", "recommendation",
            "what should i take", "what can i take", "what to register", "what to enroll",
            "next semester plan", "semester plan", "course plan",
            "best courses", "best subjects", "choose courses",
        ],
    },
    "eligibility_check": {
        "ar": [
            "اقدر اسجل", "هل اقدر اسجل", "هل استطيع اسجل", "هل مسموح اسجل",
            "مسموح لي", "ينفع اسجل", "هل ينفع اسجل", "هل اقدر اخذ", "هل اقدر اخذ المقرر",
            "هل استطيع اخذ", "هل اقدر انزل", "هل اقدر اضيف",
            "متطلب", "متطلبات", "المتطلبات", "متطلب سابق", "متطلب سابقه", "متطلب سابق",
            "قبل ما اخذ", "لازم اخذ قبل", "ايش لازم قبل",
            "prerequisite", "prerequisites", "eligible", "eligibility",
            "can i take", "can i register", "am i eligible", "allowed to take",
        ],
        "en": [
            "can i register", "can i take", "am i eligible", "eligible for",
            "prerequisite", "prerequisites", "pre-req", "requirement", "requirements",
            "allowed to enroll", "can i enroll", "can i add",
        ],
    },
    "credits_summary": {
        "ar": [
            "كم ساعه", "كم ساعة", "الساعات", "ساعاتي", "ساعات مكتمله", "ساعات مكتملة",
            "كم خلصت", "كم بقي", "كم باقي", "الباقي", "متبقي", "متبقيه", "متبقية",
            "ساعات التخرج", "متطلبات التخرج", "هل اتخرج", "قربت اتخرج",
            "ساعات اختياري", "ساعات اجباري", "اختياري", "اجباري",
            "credit", "credits", "credit hours", "hours remaining",
        ],
        "en": [
            "credits", "credit hours", "how many credits", "hours", "remaining credits",
            "graduation requirements", "am i close to graduate",
            "elective credits", "required credits",
        ],
    },
    "gpa_summary": {
        "ar": [
            "معدلي", "المعدل", "معدل تراكمي", "تراكمي", "معدل فصلي", "فصلي",
            "كم معدلي", "وش معدلي", "ايش معدلي", "احسب معدلي",
            "gpa", "cgpa", "term gpa", "cumulative gpa",
        ],
        "en": [
            "gpa", "cgpa", "cumulative gpa", "term gpa",
            "what is my gpa", "calculate my gpa", "my gpa",
        ],
    },
    "gpa_simulate": {
        "ar": [
            "لو", "اذا", "إذا", "توقع", "توقعات", "متوقع", "محاكاه", "محاكاة",
            "لو جبت", "اذا جبت", "إذا جبت", "لو اخذت", "اذا اخذت",
            "لو اخذت a", "لو اخذت b", "كم يصير معدلي", "كم بيصير معدلي",
            "كيف يصير معدلي", "لو نزلت", "اذا نزلت",
            "simulate", "simulation", "expected", "predict",
        ],
        "en": [
            "if i get", "what if", "expected gpa", "simulate", "simulation",
            "predict my gpa", "if i take", "if i score",
        ],
    },
    "snapshot": {
        "ar": [
            "وضعي", "حالتي", "حالي", "ملخص", "ملخصي", "ملخص عني", "ملخص اكاديمي",
            "تقدمي", "تقدمي الاكاديمي", "progress", "status",
            "اعطني نبذه", "اعطني نظرة", "اعطني تقرير",
            "وين وصلت", "ايش وضعي", "كيف وضعي",
            "snapshot", "overview", "summary",
        ],
        "en": [
            "snapshot", "overview", "summary", "my status", "my progress",
            "academic status", "show my progress",
        ],
    },
    "help": {
        "ar": [
            "مساعده", "مساعدة", "ساعدني", "كيف استخدم", "وش تقدر تسوي",
            "اوامر", "أوامر", "خيارات", "وش اقدر اسال", "وش اقدر اسأل",
            "help", "commands", "what can you do",
        ],
        "en": [
            "help", "how to use", "what can you do", "commands", "options",
        ],
    },
}


def _score_intent(t_norm: str, intent: str) -> Tuple[int, List[str]]:
    phrases = KW[intent]["ar"] + KW[intent]["en"]
    hits = _contains_any(t_norm, phrases)
    score = len(hits)

    if intent == "knowledge_base_query":
        if "تعريف" in t_norm or "ما معنى" in t_norm or "ما المقصود" in t_norm:
            score += 2
        if "لائحه" in t_norm or "لائحة" in t_norm or "نظام" in t_norm:
            score += 2
        if "حقوق" in t_norm or "لجنه" in t_norm or "لجنة" in t_norm:
            score += 2
        if "الدراسي" in t_norm or "العام الدراسي" in t_norm or "المستوى الدراسي" in t_norm or "النظام الدراسي" in t_norm:
            score += 2

    if intent == "eligibility_check":
        if "اسجل" in t_norm or "register" in t_norm or "enroll" in t_norm:
            score += 2
        if "متطلب" in t_norm or "prereq" in t_norm:
            score += 2

    if intent == "credits_summary":
        if "ساع" in t_norm or "credit" in t_norm:
            score += 2
        if "باق" in t_norm or "remaining" in t_norm:
            score += 1

    if intent == "gpa_summary":
        if "معدل" in t_norm or "gpa" in t_norm:
            score += 2

    if intent == "recommendations":
        if "اقترح" in t_norm or "recommend" in t_norm or "suggest" in t_norm:
            score += 2
        if "مواد" in t_norm or "مقررات" in t_norm:
            score += 1
        if "مناسب" in t_norm or "المناسبه" in t_norm or "المناسبة" in t_norm:
            score += 2
        if "الفصل الجاي" in t_norm or "الفصل القادم" in t_norm:
            score += 1

    if intent == "snapshot":
        if "ملخص" in t_norm or "overview" in t_norm or "summary" in t_norm:
            score += 2

    if intent == "gpa_simulate":
        if "لو" in t_norm or "اذا" in t_norm or "if" in t_norm:
            score += 1

    return score, hits


def detect_intent(text: str) -> Dict:
    raw = (text or "").strip()
    t_norm = _normalize_ar(raw)

    course_id = extract_course_id(raw)
    plans = extract_simulation_plans(raw)

    if plans:
        return {
            "intent": "gpa_simulate",
            "confidence": 0.97,
            "matches": {"gpa_simulate": ["plans_extracted"]},
            "scores": {"gpa_simulate": 999},
            "signals": {"plans_count": len(plans), "course_id": course_id},
        }

    intents = [
        "knowledge_base_query",
        "eligibility_check",
        "recommendations",
        "credits_summary",
        "gpa_summary",
        "snapshot",
        "help",
    ]

    scores = {}
    matches = {}
    for it in intents:
        sc, hits = _score_intent(t_norm, it)
        scores[it] = sc
        matches[it] = hits

    if course_id:
        scores["eligibility_check"] += 3
        matches["eligibility_check"].append("course_id_present")

    best_intent = max(scores, key=scores.get)
    best_score = scores[best_intent]

    if best_intent == "knowledge_base_query" and best_score >= 1:
        conf = 0.88
    elif best_score >= 6:
        conf = 0.9
    elif best_score >= 4:
        conf = 0.8
    elif best_score >= 2:
        conf = 0.65
    else:
        best_intent = "help"
        conf = 0.35

    return {
        "intent": best_intent,
        "confidence": conf,
        "matches": matches,
        "scores": scores,
        "signals": {"course_id": course_id, "plans_count": len(plans)},
    }