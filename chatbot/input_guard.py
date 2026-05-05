import re
from typing import Dict, Any, List

from chatbot.intents import detect_intent


QUESTION_SPLIT_RE = re.compile(r"[؟?\n]+|\s+(?:و|and)\s+(?=(?:هل|ما|كم|وش|ايش|ماذا|can|what|how)\b)", re.IGNORECASE)
ARABIC_GENERAL_KB_WORDS = {
    "اللائحه", "اللائحة", "لائحه", "لائحة",
    "النظام", "الانظمه", "الأنظمة", "التظلم", "التظلمات",
    "الحقوق", "حق", "اللجنة", "اللجنه", "التعريفات",
    "الفصل الصيفي", "العقوبات", "المادة", "الباب", "تعريف"
}

ARABIC_GENERAL_STUDY_WORDS = {
    "المعدل", "معدل", "الساعات", "ساعات", "المواد", "مواد",
    "التسجيل", "تسجيل", "الخطة", "الخطه", "التخرج", "المقررات", "مقرر"
}

ARABIC_VAGUE_RECOMMENDATION_WORDS = {
    "مواد", "المواد", "اقترح", "اقترحلي", "اقترح لي",
    "وش اسجل", "ايش اسجل", "ماذا اسجل", "وش اخذ", "ايش اخذ",
    "جدولي", "مواد الفصل", "الخطة", "الخطه"
}

MEANINGLESS_TOKENS = {
    "؟", "؟؟", "؟؟؟", ".", "..", "...", "....",
    "_", "__", "___", "-", "--", "---",
    "!", "!!", "!!!", ",", ",,", ",,,"
}

GREETING_ONLY_WORDS = {
    "السلام عليكم", "عليكم السلام", "صباح الخير", "مساء الخير","السلام",
    "اهلا", "أهلا", "اهلا وسهلا", "مرحبا", "مرحباً", "هلا","هاي",
    "hi", "hello", "good morning", "good evening"
}

PERSONAL_SMALL_TALK_WORDS = {
    "كيف حالك", "كيف الحال", "اخبارك", "أخبارك", "شخبارك",
    "عامل ايه", "how are you", "how are you doing", "whats up", "what's up"
}

MIXED_LANGUAGE_ENGLISH_SIGNAL_WORDS = {
    "if", "and", "what", "how", "can", "register", "rights",
    "student", "system", "plan", "semester", "gpa", "credit"
}

ALLOWED_ENGLISH_ACADEMIC_WORDS = {
    "gpa", "cgpa", "credits", "credit", "register", "course", "semester"
}

INVALID_GRADE_WORDS = {
    "ممتاز", "جيد جدا", "جيد جدًا", "جيد", "مقبول",
    "very good", "excellent", "pass", "high", "full mark"
}

VALID_GRADE_PATTERN = re.compile(
    r"\b(A\+?|A-|B\+?|B-|C\+?|C-|D\+?|D-|F|أ|ب\+|ب|ج\+|ج|د\+|د)\b",
    re.IGNORECASE
)

COURSE_ID_PATTERN = re.compile(r"\b[A-Z]{2,6}\d{3,4}\b")
NUMBER_GRADE_PATTERN = re.compile(r"\b\d{2,3}\b")

MAX_INPUT_LENGTH = 350
MAX_INPUT_WORDS = 70

STUDY_PLAN_INTENTS = {
    "snapshot",
    "credits_summary",
    "gpa_summary",
    "gpa_simulate",
    "eligibility_check",
    "recommendations"
}

OUT_OF_SCOPE_PATTERNS = [
    "افضل لاعب", "أفضل لاعب", "مباراه", "مباراة", "كرة قدم",
    "عاصمه", "عاصمة", "دوله", "دولة",
    "كم الساعه", "كم الساعة", "الوقت الان", "الوقت الآن",
    "اكتب لي مقال", "اكتب مقال", "اكتب موضوع", "اكتب بحث",
    "وصفه", "وصفة", "طبخ", "اكل", "أكل",
    "سعر الدولار", "سعر اليورو", "طقس", "الجو",
    "who is the best player", "write me an essay", "what time is it",
    "capital of", "weather", "recipe", "stock price", "football"
]

ARABIC_CHARS_RE = re.compile(r"[\u0600-\u06FF]")
ENGLISH_CHARS_RE = re.compile(r"[A-Za-z]")

def _normalize_text(text: str) -> str:
    if not text:
        return ""

    t = text.strip()

    t = t.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    t = t.replace("ة", "ه")
    t = t.replace("ى", "ي")

    t = re.sub(r"\s+", " ", t).strip()
    return t

def _tokenize(text: str) -> List[str]:
    t = _normalize_text(text)
    if not t:
        return []
    return [w for w in t.split() if w.strip()]


def _is_meaningless_text(text: str) -> bool:
    t = (text or "").strip()

    if not t:
        return True

    stripped = re.sub(r"[\s؟?.,!،؛:_\-_/\\|@#$%^&*+=~`]+", "", t)
    if not stripped:
        return True

    lowered = t.lower().strip()
    if lowered in {"null", "none", "empty"}:
        return True

    return False


def _symbol_ratio(text: str) -> float:
    t = text or ""
    if not t:
        return 0.0

    total = len(t)
    symbol_count = len(re.findall(r"[^\w\s\u0600-\u06FF]", t, flags=re.UNICODE))
    return symbol_count / total if total > 0 else 0.0


def _has_heavy_repetition(text: str) -> bool:
    t = _normalize_text(text)
    tokens = _tokenize(t)

    if not tokens:
        return False

    if len(tokens) >= 3:
        unique_tokens = set(tokens)
        if len(unique_tokens) == 1:
            return True

    repeated_char = re.search(r"(.)\1{5,}", t)
    if repeated_char:
        return True

    laughter_patterns = [
        r"(هه){3,}",
        r"(خخ){3,}",
        r"(ha){3,}",
        r"(lo){2,}l+",
        r"(aa){3,}"
    ]
    for pattern in laughter_patterns:
        if re.search(pattern, t, re.IGNORECASE):
            return True

    return False


def _is_too_short_message(text: str) -> bool:
    tokens = _tokenize(text)

    if not tokens:
        return False

    if len(tokens) == 1:
        return True

    if len(tokens) == 2:
        joined = " ".join(tokens)
        if len(joined) <= 10:
            return True

    return False

def _detect_empty_or_meaningless_input(message: str) -> Dict[str, Any]:
    if _is_meaningless_text(message):
        return {"found": True}
    return {"found": False}

def _detect_noisy_or_repetitive_input(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)

    if _has_heavy_repetition(t):
        return {"found": True}

    return {"found": False}

def _detect_symbol_heavy_input(message: str) -> Dict[str, Any]:
    ratio = _symbol_ratio(message)

    if ratio >= 0.35:
        return {
            "found": True,
            "symbol_ratio": round(ratio, 2)
        }

    return {
        "found": False,
        "symbol_ratio": round(ratio, 2)
    }


def _detect_too_short_or_ambiguous(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    tokens = _tokenize(t)

    if not tokens:
        return {"found": False}

    det = detect_intent(t)
    intent = det.get("intent", "help")
    confidence = det.get("confidence", 0)

    if _is_too_short_message(t) and intent == "help":
        return {
            "found": True,
            "intent": intent,
            "confidence": confidence
        }

    if len(tokens) <= 2 and confidence <= 0.4:
        return {
            "found": True,
            "intent": intent,
            "confidence": confidence
        }

    if t in {"تعريف", "اشرح", "وش الحل", "ساعدني", "مساعده", "مساعدة"}:
        return {
            "found": True,
            "intent": intent,
            "confidence": confidence
        }

    return {
        "found": False,
        "intent": intent,
        "confidence": confidence
    }

def _detect_overly_broad_kb_query(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    tokens = _tokenize(t)

    if not tokens:
        return {"found": False}

    det = detect_intent(t)
    intent = det.get("intent", "help")

    if len(tokens) <= 2:
        if t in ARABIC_GENERAL_KB_WORDS:
            return {
                "found": True,
                "intent": intent
            }

    return {
        "found": False,
        "intent": intent
    }


def _detect_overly_broad_study_plan_query(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    tokens = _tokenize(t)

    if not tokens:
        return {"found": False}

    det = detect_intent(t)
    intent = det.get("intent", "help")

    if len(tokens) <= 2:
        if t in ARABIC_GENERAL_STUDY_WORDS:
            return {
                "found": True,
                "intent": intent
            }

    return {
        "found": False,
        "intent": intent
    }


def _detect_vague_recommendation_request(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    tokens = _tokenize(t)

    if not tokens:
        return {"found": False}

    det = detect_intent(t)
    intent = det.get("intent", "help")

    if len(tokens) <= 3:
        if t in ARABIC_VAGUE_RECOMMENDATION_WORDS:
            return {
                "found": True,
                "intent": intent
            }

    recommendation_markers = ["اقترح", "وش اسجل", "ايش اسجل", "ماذا اسجل", "مواد"]
    if len(tokens) <= 3 and any(marker in t for marker in recommendation_markers):
        return {
            "found": True,
            "intent": intent
        }

    return {
        "found": False,
        "intent": intent
    }



def _split_possible_questions(text: str) -> List[str]:
    t = _normalize_text(text)
    if not t:
        return []

    parts = QUESTION_SPLIT_RE.split(t)
    cleaned_parts = []

    for part in parts:
        p = part.strip(" .,!،؛:؟?")
        if len(p) >= 2:
            cleaned_parts.append(p)

    return cleaned_parts


def _looks_like_real_question(text: str) -> bool:
    t = _normalize_text(text)

    if not t:
        return False

    indicators = [
        "هل", "ما", "ماذا", "وش", "ايش", "كم", "كيف", "متى",
        "can", "what", "how", "when", "why"
    ]

    if any(ind in t.lower() for ind in indicators):
        return True

    det = detect_intent(t)
    return det.get("intent") != "help" and det.get("confidence", 0) >= 0.6


def _detect_multiple_questions(message: str) -> Dict[str, Any]:
    parts = _split_possible_questions(message)

    real_questions = [p for p in parts if _looks_like_real_question(p)]

    if len(real_questions) >= 2:
        return {
            "found": True,
            "questions": real_questions
        }

    return {
        "found": False,
        "questions": []
    }


def _detect_mixed_agent_question(message: str) -> Dict[str, Any]:
    parts = _split_possible_questions(message)

    if len(parts) < 2:
        return {
            "found": False,
            "questions": [],
            "agents": []
        }

    detected_questions = []
    detected_agents = []

    for part in parts:
        det = detect_intent(part)
        intent = det.get("intent", "help")

        if intent == "help":
            continue

        agent = "knowledge_base" if intent == "knowledge_base_query" else "study_plan"

        detected_questions.append({
            "text": part,
            "intent": intent,
            "agent": agent
        })
        detected_agents.append(agent)

    unique_agents = list(set(detected_agents))

    if len(detected_questions) >= 2 and len(unique_agents) >= 2:
        return {
            "found": True,
            "questions": detected_questions,
            "agents": unique_agents
        }

    return {
        "found": False,
        "questions": detected_questions,
        "agents": unique_agents
    }


def _detect_greeting_only(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)

    if not t:
        return {"found": False}

    if t.lower() in {w.lower() for w in GREETING_ONLY_WORDS}:
        return {"found": True}

    return {"found": False}



def _detect_personal_small_talk(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)

    if not t:
        return {"found": False}

    if t.lower() in {w.lower() for w in PERSONAL_SMALL_TALK_WORDS}:
        return {"found": True}

    return {"found": False}


def _looks_like_gpa_simulation_request(message: str) -> bool:
    t = _normalize_text(message).lower()

    markers = [
        "لو جبت", "اذا جبت", "إذا جبت", "لو اخذت", "اذا اخذت", "إذا اخذت",
        "كم يصير معدلي", "كم بيصير معدلي", "المعدل المتوقع",
        "simulate", "simulation", "expected gpa", "if i get", "what if"
    ]

    if any(marker.lower() in t for marker in markers):
        return True

    if "=" in t and COURSE_ID_PATTERN.search(t):
        return True

    return False


def _detect_incomplete_gpa_simulation(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)

    if not _looks_like_gpa_simulation_request(t):
        return {"found": False}

    course_ids = COURSE_ID_PATTERN.findall(t)
    valid_grades = VALID_GRADE_PATTERN.findall(t)

    if not course_ids and valid_grades:
        return {
            "found": True,
            "reason": "grades_without_courses"
        }

    if course_ids and not valid_grades:
        return {
            "found": True,
            "reason": "courses_without_grades"
        }

    if ("لو" in t or "اذا" in t or "إذا" in t) and len(valid_grades) == 1 and len(course_ids) == 0:
        return {
            "found": True,
            "reason": "simulation_phrase_without_course"
        }

    if "=" in t and len(course_ids) != len(valid_grades):
        return {
            "found": True,
            "reason": "incomplete_pairing"
        }

    return {"found": False}



def _detect_unpaired_courses_and_grades(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)

    if not _looks_like_gpa_simulation_request(t):
        return {"found": False}

    course_ids = COURSE_ID_PATTERN.findall(t)
    valid_grades = VALID_GRADE_PATTERN.findall(t)

    if not course_ids and not valid_grades:
        return {"found": False}

    if len(course_ids) == 0 and len(valid_grades) >= 1:
        return {
            "found": True,
            "reason": "grades_only"
        }

    if len(course_ids) >= 1 and len(valid_grades) == 0:
        return {
            "found": True,
            "reason": "courses_only"
        }

    if len(course_ids) != len(valid_grades):
        return {
            "found": True,
            "reason": "count_mismatch"
        }

    return {"found": False}

def _detect_invalid_grade_format(message: str) -> Dict[str, Any]:
    t = _normalize_text(message).lower()

    if not _looks_like_gpa_simulation_request(t):
        return {"found": False}

    invalid_words_found = [w for w in INVALID_GRADE_WORDS if w.lower() in t]
    numeric_grades_found = NUMBER_GRADE_PATTERN.findall(t)

    if invalid_words_found:
        return {
            "found": True,
            "reason": "invalid_grade_words",
            "invalid_values": invalid_words_found
        }

    if numeric_grades_found:
        return {
            "found": True,
            "reason": "numeric_grade_values",
            "invalid_values": numeric_grades_found
        }

    return {"found": False}

def _detect_course_id_only(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    course_ids = COURSE_ID_PATTERN.findall(t)

    if len(course_ids) == 1:
        tokens = _tokenize(t)

        if len(tokens) == 1 and tokens[0].upper() == course_ids[0]:
            return {
                "found": True,
                "course_id": course_ids[0]
            }

    return {
        "found": False,
        "course_id": None
    }

def _detect_invalid_student_id(student_id: int) -> Dict[str, Any]:
    try:
        sid = int(student_id)
    except Exception:
        return {
            "found": True,
            "reason": "not_integer"
        }

    if sid <= 0:
        return {
            "found": True,
            "reason": "non_positive"
        }

    return {
        "found": False,
        "reason": None
    }


def _detect_missing_required_context(message: str, student_id: int) -> Dict[str, Any]:
    if message is None:
        return {
            "found": True,
            "reason": "missing_message"
        }

    if not isinstance(message, str):
        return {
            "found": True,
            "reason": "message_not_string"
        }

    if student_id is None:
        return {
            "found": True,
            "reason": "missing_student_id"
        }

    return {
        "found": False,
        "reason": None
    }

def _detect_multiple_course_ids_without_clear_request(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    course_ids = COURSE_ID_PATTERN.findall(t)

    if len(course_ids) >= 2:
        det = detect_intent(t)
        intent = det.get("intent", "help")
        confidence = det.get("confidence", 0)

        if intent == "help" or confidence < 0.6:
            return {
                "found": True,
                "course_ids": course_ids
            }

        has_question_words = any(
            marker in t.lower()
            for marker in ["هل", "ما", "كم", "وش", "ايش", "ماذا", "can", "what", "how"]
        )

        has_equal_sign = "=" in t
        has_grade = bool(VALID_GRADE_PATTERN.search(t))

        if not has_question_words and not has_equal_sign and not has_grade:
            return {
                "found": True,
                "course_ids": course_ids
            }

    return {
        "found": False,
        "course_ids": []
    }

def _detect_too_long_input(message: str) -> Dict[str, Any]:
    t = message or ""
    tokens = _tokenize(t)

    if len(t) > MAX_INPUT_LENGTH:
        return {
            "found": True,
            "reason": "char_limit_exceeded",
            "length": len(t),
            "words": len(tokens)
        }

    if len(tokens) > MAX_INPUT_WORDS:
        return {
            "found": True,
            "reason": "word_limit_exceeded",
            "length": len(t),
            "words": len(tokens)
        }

    return {
        "found": False,
        "reason": None,
        "length": len(t),
        "words": len(tokens)
    }

def _detect_too_complex_input(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    tokens = _tokenize(t)

    if not tokens:
        return {"found": False}

    det = detect_intent(t)
    course_ids = COURSE_ID_PATTERN.findall(t)

    question_markers = ["هل", "ما", "كم", "وش", "ايش", "ماذا", "كيف", "متى"]
    marker_count = sum(1 for marker in question_markers if marker in t)

    and_count = t.count(" و ")
    has_kb_terms = any(word in t for word in ARABIC_GENERAL_KB_WORDS)
    has_study_terms = any(word in t for word in ARABIC_GENERAL_STUDY_WORDS)

    complexity_score = 0

    if len(tokens) >= 30:
        complexity_score += 1
    if marker_count >= 3:
        complexity_score += 1
    if and_count >= 3:
        complexity_score += 1
    if len(course_ids) >= 2:
        complexity_score += 1
    if has_kb_terms and has_study_terms:
        complexity_score += 1
    if det.get("confidence", 0) < 0.5 and len(tokens) >= 20:
        complexity_score += 1

    if complexity_score >= 3:
        return {
            "found": True,
            "complexity_score": complexity_score
        }

    return {
        "found": False,
        "complexity_score": complexity_score
    }

def _count_arabic_chars(text: str) -> int:
    return len(ARABIC_CHARS_RE.findall(text or ""))


def _count_english_chars(text: str) -> int:
    return len(ENGLISH_CHARS_RE.findall(text or ""))

def _detect_unreadable_mixed_language_input(message: str) -> Dict[str, Any]:
    t = message or ""
    normalized = _normalize_text(t)
    tokens = _tokenize(normalized)

    if not tokens:
        return {"found": False}

    arabic_words = re.findall(r"[\u0600-\u06FF]+", normalized)
    english_words = re.findall(r"\b[A-Za-z]+\b", normalized)
    course_ids = COURSE_ID_PATTERN.findall(normalized)

    arabic_count = len(arabic_words)
    english_count = len(english_words)

    if arabic_count == 0 or english_count == 0:
        return {
            "found": False,
            "arabic_count": arabic_count,
            "english_count": english_count
        }

    english_signal_hits = [
        w for w in english_words
        if w.lower() in MIXED_LANGUAGE_ENGLISH_SIGNAL_WORDS
    ]

    det = detect_intent(normalized)
    confidence = det.get("confidence", 0)

    has_kb_terms = any(word in normalized for word in ARABIC_GENERAL_KB_WORDS)
    has_study_terms = any(word in normalized for word in ARABIC_GENERAL_STUDY_WORDS)
    has_simulation_markers = _looks_like_gpa_simulation_request(normalized)

    complexity_flags = 0

    if len(english_signal_hits) >= 2 and arabic_count >= 1:
        complexity_flags += 1

    if has_kb_terms and has_study_terms:
        complexity_flags += 1

    if has_simulation_markers and has_kb_terms:
        complexity_flags += 1

    if confidence <= 0.65 and english_count >= 2 and arabic_count >= 1:
        complexity_flags += 1

    if len(tokens) >= 6 and english_count >= 3 and arabic_count >= 2:
        complexity_flags += 1

    if complexity_flags >= 2:
        return {
            "found": True,
            "arabic_count": arabic_count,
            "english_count": english_count,
            "confidence": confidence,
            "english_signal_hits": english_signal_hits,
            "complexity_flags": complexity_flags,
            "course_ids": course_ids
        }

    return {
        "found": False,
        "arabic_count": arabic_count,
        "english_count": english_count,
        "confidence": confidence,
        "english_signal_hits": english_signal_hits,
        "complexity_flags": complexity_flags,
        "course_ids": course_ids
    }


def _detect_unparsable_input(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)
    tokens = _tokenize(t)

    if not tokens:
        return {"found": False}

    det = detect_intent(t)
    confidence = det.get("confidence", 0)
    intent = det.get("intent", "help")

    has_question_marker = any(
        marker in t.lower()
        for marker in ["هل", "ما", "ماذا", "وش", "ايش", "كم", "كيف", "متى", "what", "how", "can", "?","؟"]
    )

    arabic_words = re.findall(r"[\u0600-\u06FF]+", t)
    english_words = re.findall(r"\b[A-Za-z]+\b", t)
    course_ids = COURSE_ID_PATTERN.findall(t)
    valid_grades = VALID_GRADE_PATTERN.findall(t)

    disconnected_tokens = 0
    for token in tokens:
        token_clean = token.strip().lower()
        if (
            token_clean not in MIXED_LANGUAGE_ENGLISH_SIGNAL_WORDS
            and token_clean not in {w.lower() for w in ALLOWED_ENGLISH_ACADEMIC_WORDS}
            and not re.search(r"[\u0600-\u06FF]", token_clean)
            and not re.search(r"[A-Za-z]", token_clean)
            and not re.search(r"\d", token_clean)
        ):
            disconnected_tokens += 1

    weird_structure_flags = 0

    if intent == "help" and confidence <= 0.4 and len(tokens) >= 3:
        weird_structure_flags += 1

    if not has_question_marker and len(tokens) >= 4 and len(course_ids) == 0 and len(valid_grades) == 0:
        weird_structure_flags += 1

    if len(arabic_words) + len(english_words) <= 2 and len(tokens) >= 4:
        weird_structure_flags += 1

    if disconnected_tokens >= 2:
        weird_structure_flags += 1

    if weird_structure_flags >= 2:
        return {
            "found": True,
            "reason": "unparsable_structure",
            "confidence": confidence,
            "intent": intent,
            "weird_structure_flags": weird_structure_flags
        }

    return {
        "found": False,
        "reason": None,
        "confidence": confidence,
        "intent": intent,
        "weird_structure_flags": weird_structure_flags
    }
def _detect_out_of_scope_request(message: str) -> Dict[str, Any]:
    t = _normalize_text(message)

    if not t:
        return {"found": False}

    for pattern in OUT_OF_SCOPE_PATTERNS:
        if pattern.lower() in t.lower():
            return {
                "found": True,
                "matched_pattern": pattern
            }

    det = detect_intent(t)
    intent = det.get("intent", "help")
    confidence = det.get("confidence", 0)

    out_of_scope_keywords = [
        "لاعب", "مباراة", "كرة", "طقس", "الجو", "الدولار", "اليورو",
        "طبخ", "وصفة", "مقال", "فرنسا", "عاصمة", "رياضة",
        "player", "match", "football", "weather", "recipe", "essay", "capital"
    ]

    if intent == "help" and confidence <= 0.4:
        for kw in out_of_scope_keywords:
            if kw.lower() in t.lower():
                return {
                    "found": True,
                    "matched_pattern": kw
                }

    return {
        "found": False,
        "matched_pattern": None
    }
def validate_user_input(message: str, student_id: int, language: str = "ar") -> Dict[str, Any]:
    ar = (language or "ar").lower().startswith("ar")
    normalized_message = _normalize_text(message)

    missing_context_check = _detect_missing_required_context(message, student_id)
    if missing_context_check["found"]:
        return {
            "ok": False,
            "error_code": "MISSING_REQUIRED_CONTEXT",
            "message": (
                "يوجد نقص في البيانات المطلوبة لتنفيذ الطلب. الرجاء التأكد من إدخال الرسالة ورقم الطالب بشكل صحيح."
                if ar else
                "Some required input data is missing. Please make sure the message and student ID are provided correctly."
            ),
            "details": {
                "reason": missing_context_check.get("reason")
            }
        }

    invalid_student_check = _detect_invalid_student_id(student_id)
    if invalid_student_check["found"]:
        return {
            "ok": False,
            "error_code": "INVALID_STUDENT_ID",
            "message": (
                "رقم الطالب غير موجود أو غير صالح. الرجاء إدخال رقم طالب صحيح."
                if ar else
                "The student ID is missing or invalid. Please provide a valid student ID."
            ),
            "details": {
                "reason": invalid_student_check.get("reason")
            }
        }

    empty_check = _detect_empty_or_meaningless_input(normalized_message)
    if empty_check["found"]:
        return {
            "ok": False,
            "error_code": "EMPTY_OR_MEANINGLESS_INPUT",
            "message": (
                "الرسالة فارغة أو غير واضحة. الرجاء كتابة سؤالك بشكل كامل."
                if ar else
                "Your message is empty or unclear. Please write a complete question."
            ),
            "details": {}
        }

    greeting_check = _detect_greeting_only(normalized_message)
    if greeting_check["found"]:
        return {
            "ok": False,
            "error_code": "GREETING_ONLY",
            "message": (
                "وعليكم السلام ورحمة الله وبركاته. أهلاً بك، اكتب سؤالك الأكاديمي أو سؤالك عن اللائحة وسأساعدك."
                if ar else
                "Hello. Please write your academic or regulation-related question and I will help you."
            ),
            "details": {}
        }

    small_talk_check = _detect_personal_small_talk(normalized_message)
    if small_talk_check["found"]:
        return {
            "ok": False,
            "error_code": "PERSONAL_SMALL_TALK",
            "message": (
                "أنا بخير، شكرًا لك. اكتب سؤالك عن الخطة الدراسية أو اللائحة الأكاديمية وسأساعدك."
                if ar else
                "I'm doing well, thank you. Please write your study-plan or academic regulation question."
            ),
            "details": {}
        }

    symbol_check = _detect_symbol_heavy_input(normalized_message)
    if symbol_check["found"]:
        return {
            "ok": False,
            "error_code": "SYMBOL_HEAVY_INPUT",
            "message": (
                "رسالتك تحتوي على عدد كبير من الرموز، وهذا يجعل فهمها صعبًا. الرجاء إعادة كتابة السؤال بشكل أوضح."
                if ar else
                "Your message contains too many symbols. Please rewrite it more clearly."
            ),
            "details": {
                "symbol_ratio": symbol_check.get("symbol_ratio", 0)
            }
        }

    noisy_check = _detect_noisy_or_repetitive_input(normalized_message)
    if noisy_check["found"]:
        return {
            "ok": False,
            "error_code": "NOISY_OR_REPETITIVE_INPUT",
            "message": (
                "يبدو أن الرسالة تحتوي على تكرار أو ضوضاء كثيرة. الرجاء كتابة سؤالك مرة واحدة وبشكل مباشر."
                if ar else
                "Your message seems too repetitive or noisy. Please write your question once and clearly."
            ),
            "details": {}
        }

    invalid_grade_check = _detect_invalid_grade_format(normalized_message)
    if invalid_grade_check["found"]:
        return {
            "ok": False,
            "error_code": "INVALID_GRADE_FORMAT",
            "message": (
                "صيغة الدرجة غير مدعومة في محاكاة المعدل. الرجاء استخدام درجات مثل: A أو B+ أو C."
                if ar else
                "Unsupported grade format in GPA simulation. Please use grades such as A, B+, or C."
            ),
            "details": {
                "reason": invalid_grade_check.get("reason"),
                "invalid_values": invalid_grade_check.get("invalid_values", [])
            }
        }

    incomplete_sim_check = _detect_incomplete_gpa_simulation(normalized_message)
    if incomplete_sim_check["found"]:
        return {
            "ok": False,
            "error_code": "INCOMPLETE_GPA_SIMULATION",
            "message": (
                "طلب محاكاة المعدل غير مكتمل. الرجاء كتابة كل مادة مع درجتها المتوقعة، مثل: CS2105=A و AI2001=B."
                if ar else
                "Your GPA simulation request is incomplete. Please provide each course with its expected grade."
            ),
            "details": {
                "reason": incomplete_sim_check.get("reason")
            }
        }

    unpaired_sim_check = _detect_unpaired_courses_and_grades(normalized_message)
    if unpaired_sim_check["found"]:
        return {
            "ok": False,
            "error_code": "UNPAIRED_COURSES_AND_GRADES",
            "message": (
                "يوجد عدم تطابق بين المواد والدرجات في طلب محاكاة المعدل. الرجاء كتابة كل مادة مع درجتها بشكل واضح."
                if ar else
                "There is a mismatch between courses and grades in your GPA simulation request."
            ),
            "details": {
                "reason": unpaired_sim_check.get("reason")
            }
        }

    course_only_check = _detect_course_id_only(normalized_message)
    if course_only_check["found"]:
        return {
            "ok": False,
            "error_code": "COURSE_ID_ONLY",
            "message": (
                f"تم التعرف على كود المقرر {course_only_check.get('course_id')}, لكن الطلب غير واضح. الرجاء تحديد المطلوب، مثل: هل أقدر أسجل {course_only_check.get('course_id')}؟"
                if ar else
                "A course ID was detected, but the request is unclear. Please specify what you want."
            ),
            "details": {
                "course_id": course_only_check.get("course_id")
            }
        }

    multiple_courses_check = _detect_multiple_course_ids_without_clear_request(normalized_message)
    if multiple_courses_check["found"]:
        return {
            "ok": False,
            "error_code": "MULTIPLE_COURSE_IDS_WITHOUT_CLEAR_REQUEST",
            "message": (
                "تم التعرف على أكثر من كود مقرر، لكن المطلوب غير واضح. الرجاء تحديد الطلب بشكل صريح، مثل: هل أقدر أسجل هذه المقررات؟ أو ما هي متطلبات هذه المقررات؟"
                if ar else
                "Multiple course IDs were detected, but the request is unclear. Please state what you want explicitly."
            ),
            "details": {
                "course_ids": multiple_courses_check.get("course_ids", [])
            }
        }

    short_check = _detect_too_short_or_ambiguous(normalized_message)
    if short_check["found"]:
        return {
            "ok": False,
            "error_code": "TOO_SHORT_OR_AMBIGUOUS",
            "message": (
                "سؤالك قصير جدًا أو غير واضح. الرجاء كتابة الطلب بشكل أوضح، مثل: ما هو معدلي؟ أو ما معنى النظام الدراسي؟"
                if ar else
                "Your message is too short or unclear. Please write a clearer request."
            ),
            "details": {
                "intent": short_check.get("intent"),
                "confidence": short_check.get("confidence")
            }
        }

    vague_rec_check = _detect_vague_recommendation_request(normalized_message)
    if vague_rec_check["found"]:
        return {
            "ok": False,
            "error_code": "VAGUE_RECOMMENDATION_REQUEST",
            "message": (
                "يبدو أنك تريد توصيات مواد، لكن الطلب غير مكتمل. يمكنك كتابة مثلًا: اقترح لي 5 مواد للفصل القادم."
                if ar else
                "It looks like you want course recommendations, but the request is incomplete."
            ),
            "details": {}
        }

    mixed_lang_check = _detect_unreadable_mixed_language_input(normalized_message)
    if mixed_lang_check["found"]:
        return {
            "ok": False,
            "error_code": "UNREADABLE_MIXED_LANGUAGE_INPUT",
            "message": (
                "رسالتك تحتوي خلطًا كبيرًا بين لغات وصياغات مختلفة، وهذا يجعل فهمها غير دقيق. الرجاء إعادة كتابة السؤال بلغة وصياغة أوضح."
                if ar else
                "Your message mixes languages and structures too heavily. Please rewrite it more clearly."
            ),
            "details": {
                "arabic_count": mixed_lang_check.get("arabic_count"),
                "english_count": mixed_lang_check.get("english_count"),
                "confidence": mixed_lang_check.get("confidence"),
                "english_signal_hits": mixed_lang_check.get("english_signal_hits", []),
                "complexity_flags": mixed_lang_check.get("complexity_flags")
            }
        }

    unparsable_check = _detect_unparsable_input(normalized_message)
    if unparsable_check["found"]:
        return {
            "ok": False,
            "error_code": "UNPARSABLE_INPUT",
            "message": (
                "لم أتمكن من فهم صياغة الرسالة بشكل كافٍ. الرجاء إعادة كتابة السؤال بشكل أوضح ومباشر."
                if ar else
                "I could not understand the message structure clearly enough. Please rewrite your question more directly."
            ),
            "details": {
                "reason": unparsable_check.get("reason"),
                "confidence": unparsable_check.get("confidence"),
                "intent": unparsable_check.get("intent"),
                "weird_structure_flags": unparsable_check.get("weird_structure_flags")
            }
        }

    broad_kb_check = _detect_overly_broad_kb_query(normalized_message)
    if broad_kb_check["found"]:
        return {
            "ok": False,
            "error_code": "OVERLY_BROAD_KB_QUERY",
            "message": (
                "سؤالك عام جدًا في جانب اللوائح أو الأنظمة. الرجاء تحديد المطلوب بشكل أوضح، مثل: ما هي حقوق الطلبة؟ أو ما معنى النظام الدراسي؟"
                if ar else
                "Your knowledge-base question is too broad. Please make it more specific."
            ),
            "details": {}
        }

    broad_study_check = _detect_overly_broad_study_plan_query(normalized_message)
    if broad_study_check["found"]:
        return {
            "ok": False,
            "error_code": "OVERLY_BROAD_STUDY_PLAN_QUERY",
            "message": (
                "سؤالك عام جدًا في جانب الخطة الدراسية. الرجاء تحديد المطلوب بشكل أوضح، مثل: كم ساعة باقي لي؟ أو ما هو معدلي التراكمي؟"
                if ar else
                "Your study-plan question is too broad. Please make it more specific."
            ),
            "details": {}
        }

    long_input_check = _detect_too_long_input(normalized_message)
    if long_input_check["found"]:
        return {
            "ok": False,
            "error_code": "TOO_LONG_INPUT",
            "message": (
                "رسالتك طويلة جدًا. الرجاء اختصار السؤال وكتابته بشكل مباشر حتى أتمكن من مساعدتك بشكل أدق."
                if ar else
                "Your message is too long. Please shorten it and ask your question more directly."
            ),
            "details": {
                "reason": long_input_check.get("reason"),
                "length": long_input_check.get("length"),
                "words": long_input_check.get("words")
            }
        }

    complex_input_check = _detect_too_complex_input(normalized_message)
    if complex_input_check["found"]:
        return {
            "ok": False,
            "error_code": "TOO_COMPLEX_INPUT",
            "message": (
                "رسالتك تحتوي على عدة أفكار أو تفاصيل متشابكة. الرجاء تقسيمها أو إرسال سؤال واحد بشكل أوضح."
                if ar else
                "Your message is too complex or contains too many ideas. Please simplify it or send one clearer question."
            ),
            "details": {
                "complexity_score": complex_input_check.get("complexity_score")
            }
        }


    out_of_scope_check = _detect_out_of_scope_request(normalized_message)
    if out_of_scope_check["found"]:
        return {
            "ok": False,
            "error_code": "OUT_OF_SCOPE_REQUEST",
            "message": (
                "هذا الطلب خارج نطاق نظام مرشد. يمكنني مساعدتك في أسئلة الخطة الدراسية أو اللوائح والأنظمة الأكاديمية فقط."
                if ar else
                "This request is outside Murshid's scope. I can only help with study-plan and academic regulation questions."
            ),
            "details": {
                "matched_pattern": out_of_scope_check.get("matched_pattern")
            }
        }

    multi_q = _detect_multiple_questions(normalized_message)
    if multi_q["found"]:
        mixed = _detect_mixed_agent_question(normalized_message)

        if mixed["found"]:
            return {
                "ok": False,
                "error_code": "MIXED_AGENT_QUESTION",
                "message": (
                    "رسالتك تحتوي أكثر من سؤال من نوعين مختلفين: سؤال عن اللوائح أو الأنظمة، وسؤال عن الخطة الدراسية. الرجاء إرسال كل سؤال في رسالة مستقلة."
                    if ar else
                    "Your message contains different question types. Please send one question at a time."
                ),
                "details": {
                    "questions": mixed["questions"],
                    "agents": mixed["agents"]
                }
            }

        return {
            "ok": False,
            "error_code": "MULTI_QUESTION_INPUT",
            "message": (
                "يظهر أن رسالتك تحتوي أكثر من سؤال. الرجاء إدخال سؤال واحد فقط في كل مرة حتى أستطيع إعطاءك إجابة أدق."
                if ar else
                "Your message seems to contain more than one question. Please send one question at a time."
            ),
            "details": {
                "questions": multi_q["questions"]
            }
        }

    return {
        "ok": True,
        "normalized_message": normalized_message,
        "warnings": []
    }