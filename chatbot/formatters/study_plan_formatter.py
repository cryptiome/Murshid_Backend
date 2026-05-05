from typing import Dict, Any, List, Optional

def _safe_get(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur

def _fmt_course_line(c: Dict[str, Any]) -> str:
    # course dict from API has: course_id, course_name_ar, credits, course_type...
    cid = c.get("course_id", "")
    name = c.get("course_name_ar") or c.get("course_name_en") or ""
    credits = c.get("credits", "")
    return f"{cid} — {name} ({credits} ساعات)"

def _fmt_list(items: List[str], bullet: str = "- ") -> str:
    return "\n".join([f"{bullet}{x}" for x in items])

def _reason_ar(reason: str) -> str:
    mapping = {
        "OK": "مسموح",
        "ALREADY_PASSED": "أنت ناجح فيها مسبقًا",
        "MISSING_PREREQUISITES": "ناقصك متطلبات سابقة",
        "LEVEL_TOO_HIGH": "مستوى المادة أعلى من المسموح لك الآن",
        "NOT_IN_PROGRAM": "المادة ليست ضمن خطتك",
        "UNKNOWN": "سبب غير معروف",
    }
    return mapping.get(reason, reason)

def format_study_plan_reply(
    intent: str,
    api_results: List[Dict[str, Any]],
    extracted: Dict[str, Any],
    language: str = "ar"
) -> str:
    """
    Returns final reply_text in Arabic (MVP).
    """


    if not api_results:
        return _format_no_api(intent=intent, extracted=extracted)

    
    first = api_results[0]
    ok = first.get("ok", False)
    payload = first.get("response") or {}
    status = payload.get("status")
    data = payload.get("data") or {}

    if not ok or status != "success":
        return _format_api_error(intent=intent, first=first, extracted=extracted)

    # توزيع حسب intent
    if intent == "eligibility_check":
        return _format_eligibility(data, extracted)
    if intent == "recommendations":
        return _format_recommendations(data, extracted)
    if intent == "credits_summary":
        return _format_credits(data)
    if intent == "gpa_summary":
        return _format_gpa(data)
    if intent == "gpa_simulate":
        return _format_gpa_simulate(data, extracted)
    if intent == "snapshot":
        return _format_snapshot(data)
    if intent == "help":
        return _format_help()

    # fallback
    return _format_generic_success(data, intent=intent)

def _format_no_api(intent: str, extracted: Dict[str, Any]) -> str:
    if intent == "help":
        return _format_help()
    # unresolved
    course_id = extracted.get("course_id")
    if course_id:
        return f"وصلتني رسالتك. بس قبل ما أجاوب: هل تقصد **التأكد من أهلية تسجيل {course_id}**؟"
    return "وصلتني رسالتك، بس محتاج توضيح بسيط: هل تبغى (أهلية تسجيل) أو (اقتراح مواد) أو (معدل/ساعات)؟"

def _format_api_error(intent: str, first: Dict[str, Any], extracted: Dict[str, Any]) -> str:
   
    course_id = extracted.get("course_id")
    if intent == "eligibility_check" and course_id:
        return f"صار خطأ وأنا أحاول أتحقق من أهلية تسجيل **{course_id}**. جرّب مرة ثانية بعد قليل."
    if intent == "gpa_simulate":
        return "صار خطأ وأنا أحاول أسوي محاكاة للمعدل. تأكد أنك كتبت المواد مع التقديرات مثل: A / B / C."
    return "صار خطأ في جلب بياناتك الأكاديمية. جرّب مرة ثانية."

def _format_eligibility(data: Dict[str, Any], extracted: Dict[str, Any]) -> str:
    course = data.get("course") or {}
    cid = data.get("course_id") or extracted.get("course_id") or course.get("course_id", "")
    eligible = data.get("eligible", False)
    reason = data.get("reason", "UNKNOWN")
    missing = data.get("missing_prereqs") or []

    if reason == "ALREADY_PASSED":
        return f" لا، ما تقدر تسجل **{cid}** لأنك **ناجح فيها مسبقًا**."

    if eligible:

        prereqs = data.get("prerequisites") or course.get("prerequisites") or []
        prereq_note = ""
        if prereqs:
            prereq_note = f"\n المتطلبات السابقة مكتملة: {', '.join(prereqs)}"
        return f" نعم، تقدر تسجل **{cid}**.{prereq_note}"

    if reason == "MISSING_PREREQUISITES":
        if missing:
            return f" حاليًا ما تقدر تسجل **{cid}**.\nناقصك المتطلبات السابقة:\n{_fmt_list(missing)}"
        return f" حاليًا ما تقدر تسجل **{cid}** بسبب متطلبات سابقة غير مكتملة."

    # أسباب أخرى
    return f" حاليًا ما تقدر تسجل **{cid}**.\nالسبب: {_reason_ar(reason)}"

def _format_recommendations(data: Dict[str, Any], extracted: Dict[str, Any]) -> str:
    rec = data.get("recommended") or []
    rules = data.get("rules") or {}
    summary = data.get("summary") or {}

    if not rec:
        return "ما قدرت أطلع لك مواد مقترحة الآن (يمكن لأن كل المواد المتاحة محجوبة بشروط)."

    lines = []
    for i, c in enumerate(rec, start=1):
        lines.append(f"{i}) {_fmt_course_line(c)}")

    max_credits = rules.get("recommended_max_credits", 15)
    total_credits = summary.get("recommended_total_credits")

    note = f"\n\n ملاحظة: الحد المقترح للساعات هذا الفصل ≈ {max_credits}"
    if total_credits is not None:
        note += f"\nإجمالي ساعات المواد المقترحة: {total_credits}"


    return "هذه أفضل المواد المقترحة لك للفصل القادم حسب وضعك الحالي:\n" + "\n".join(lines) + note

def _format_credits(data: Dict[str, Any]) -> str:
    prog_name = data.get("program_name", "")
    totals = data.get("totals") or {}
    completed = data.get("completed") or {}
    remaining = data.get("remaining") or {}

    total_prog = totals.get("program_total_credits")
    major_elec = totals.get("program_major_elective_credits")

    done_total = completed.get("total")
    done_req = completed.get("required")
    done_ele = completed.get("elective")

    rem_total = remaining.get("total")
    rem_ele = remaining.get("elective")

    msg = []
    msg.append(f" ملخص الساعات — برنامج: {prog_name}")
    if total_prog is not None:
        msg.append(f"- إجمالي الخطة: {total_prog} ساعة")
    if done_total is not None:
        msg.append(f"- الساعات المنجزة: {done_total} (إجباري: {done_req} | اختياري: {done_ele})")
    if rem_total is not None:
        msg.append(f"- الساعات المتبقية للتخرج: {rem_total}")
    if major_elec is not None:
        msg.append(f"- الساعات الاختيارية المطلوبة (Major Electives): {major_elec}")
    if rem_ele is not None:
        msg.append(f"- الساعات الاختيارية المتبقية: {rem_ele}")

    return "\n".join(msg)

def _format_gpa(data: Dict[str, Any]) -> str:
    official = data.get("official") or {}
    term = official.get("term_gpa") or {}
    cum = official.get("cumulative_gpa") or {}

    term4 = term.get("term_gpa_4")
    term100 = term.get("term_gpa_100")
    cum4 = cum.get("cumulative_gpa_4")
    cum100 = cum.get("cumulative_gpa_100")

    current_sem = data.get("current_semester")

    msg = []
    msg.append(f" معدلك الحالي (الفصل {current_sem}):")
    if term4 is not None:
        msg.append(f"- المعدل الفصلي (من 4): {round(float(term4), 2)}")
    if term100 is not None:
        msg.append(f"- المعدل الفصلي (من 100): {round(float(term100), 2)}")
    if cum4 is not None:
        msg.append(f"- المعدل التراكمي (من 4): {round(float(cum4), 2)}")
    if cum100 is not None:
        msg.append(f"- المعدل التراكمي (من 100): {round(float(cum100), 2)}")

    return "\n".join(msg)

def _format_gpa_simulate(data: Dict[str, Any], extracted: Dict[str, Any]) -> str:
    expected = data.get("expected") or {}
    delta = data.get("delta") or {}
    details = data.get("details") or []

    term4 = expected.get("term_gpa_4")
    cum4 = expected.get("cumulative_gpa_4")
    change = delta.get("cumulative_gpa_4_change")

    msg = []
    msg.append(" نتيجة محاكاة المعدل:")
    if term4 is not None:
        msg.append(f"- المعدل الفصلي المتوقع (4): {round(float(term4), 2)}")
    if cum4 is not None:
        msg.append(f"- المعدل التراكمي المتوقع (4): {round(float(cum4), 2)}")
    if change is not None:
        msg.append(f"- التغير على التراكمي: {round(float(change), 4)}")

    if details:
        msg.append("\nتفاصيل المواد:")
        for d in details:
            cid = d.get("course_id")
            credits = d.get("credits")
            grade = d.get("expected_grade")
            gp = d.get("expected_grade_points")
            msg.append(f"- {cid} ({credits} ساعات): {grade} → نقاط {gp}")

    # لو فيه تحذيرات
    warnings = data.get("warnings") or {}
    warn_lines = []
    for key in ["course_not_in_program", "invalid_grade", "missing_course_credits"]:
        arr = warnings.get(key) or []
        if arr:
            warn_lines.append(f"{key}: {arr}")

    if warn_lines:
        msg.append("\n ملاحظات:")
        msg.append("\n".join([f"- {w}" for w in warn_lines]))

    return "\n".join(msg)

def _format_snapshot(data: Dict[str, Any]) -> str:

    student = data.get("student") or {}
    program = data.get("program") or {}
    term = data.get("term_gpa") or {}
    cum = data.get("cumulative_gpa") or {}

    name = student.get("name_ar", "")
    level = student.get("level")
    status = student.get("status_computed")
    completed = student.get("completed_credits")

    prog_name = program.get("program_name")
    total_credits = program.get("total_credits")

    msg = []
    msg.append(f" ملخص وضعك الأكاديمي:")
    msg.append(f"- الاسم: {name}")
    if prog_name:
        msg.append(f"- البرنامج: {prog_name}")
    if level is not None:
        msg.append(f"- المستوى: {level}")
    if status:
        msg.append(f"- الحالة: {status}")
    if completed is not None:
        msg.append(f"- الساعات المنجزة: {completed}")
    if total_credits is not None:
        msg.append(f"- إجمالي الخطة: {total_credits}")


    t4 = term.get("term_gpa_4")
    c4 = cum.get("cumulative_gpa_4")
    if t4 is not None:
        msg.append(f"- المعدل الفصلي (4): {round(float(t4), 2)}")
    if c4 is not None:
        msg.append(f"- المعدل التراكمي (4): {round(float(c4), 2)}")

    return "\n".join(msg)

def _format_help() -> str:
    return (
        "أقدر أساعدك في أسئلة الخطة الدراسية مثل:\n"
        "- هل أقدر أسجل CS2105؟\n"
        "- اقترح 5 مواد للفصل القادم\n"
        "- كم ساعة باقي لي للتخرج؟\n"
        "- معدلي التراكمي كم؟\n"
        "- لو جبت A في CS2105 و B في AI2001 كم يصير معدلي؟\n\n"
        "اكتب سؤالك مباشرة وبالعربي أو بالإنجليزي."
    )

def _format_generic_success(data: Dict[str, Any], intent: str) -> str:

    return "تم. إذا تبغى أطلع لك التفاصيل أكثر، قلّي بالضبط ايش تبي: (مواد مقترحة / أهلية مادة / معدل / ساعات)."
