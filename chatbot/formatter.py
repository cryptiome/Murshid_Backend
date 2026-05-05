from typing import Dict, Any, List


def format_reply(
    language: str,
    agent: str,
    intent: str,
    extracted: Dict[str, Any],
    api_results: List[Dict[str, Any]]
) -> str:
    ar = (language or "ar").lower().startswith("ar")

    if not api_results:
        if ar:
            return "ما قدرت أوصل للبيانات الآن. جرّب مرة ثانية."
        return "I could not access the data right now."

    for res in api_results:
        if not res.get("ok"):
            if ar:
                return "صار عندي مشكلة بسيطة أثناء جلب البيانات. جرّب مرة ثانية أو عطيني نفس سؤالك بصيغة ثانية."
            return "I had an issue fetching the data. Please try again."

    main = api_results[0]["response"]
    data = (main or {}).get("data", {})

    if agent == "knowledge_base":
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        retrieved_count = data.get("retrieved_count", 0)
        mode = data.get("mode", "")

        if not answer:
            if ar:
                return "لم أجد إجابة واضحة في اللائحة المسترجعة."
            return "I could not find a clear answer in the retrieved regulation."

        lines = [answer]

        if sources:
            first_source = sources[0]
            regulation = first_source.get("regulation", "")
            chapter = first_source.get("chapter", "")
            article = first_source.get("article", "")

            if ar:
                lines.append("")
                lines.append("المصدر:")
                if regulation:
                    lines.append(f"- اللائحة: {regulation}")
                if chapter:
                    lines.append(f"- الفصل: {chapter}")
                if article:
                    lines.append(f"- المادة: {article}")
                if retrieved_count:
                    lines.append(f"- عدد النتائج المسترجعة: {retrieved_count}")
                if mode:
                    lines.append(f"- وضع الإجابة: {mode}")
            else:
                lines.append("")
                lines.append("Source:")
                if regulation:
                    lines.append(f"- Regulation: {regulation}")
                if chapter:
                    lines.append(f"- Chapter: {chapter}")
                if article:
                    lines.append(f"- Article: {article}")
                if retrieved_count:
                    lines.append(f"- Retrieved results: {retrieved_count}")
                if mode:
                    lines.append(f"- Mode: {mode}")

        return "\n".join(lines)

    if ar:
        if intent == "eligibility_check":
            cid = extracted.get("course_id")
            eligible = data.get("eligible")
            reason = data.get("reason")
            missing = data.get("missing_prereqs", [])
            already = data.get("already_passed", False)

            if already:
                return f" المقرر {cid} **تم اجتيازه مسبقًا**، لذلك لا تحتاج تسجله مرة ثانية."
            if eligible:
                return f" نعم، تقدر تسجل **{cid}**. المتطلبات السابقة مكتملة."
            if reason == "MISSING_PREREQUISITES":
                return f" لا، ما تقدر تسجل **{cid}** الآن.\nالمتطلبات الناقصة: {', '.join(missing) if missing else 'غير محددة'}"
            if reason == "COURSE_NOT_IN_PROGRAM":
                return f" المقرر **{cid}** غير موجود ضمن خطتك/تخصصك."
            return f" لا، حاليًا غير مؤهل لتسجيل **{cid}**. السبب: {reason}"

        if intent == "recommendations":
            rec = data.get("recommended", [])
            rules = data.get("rules", {})
            if not rec:
                return "ما لقيت مواد مناسبة حاليًا حسب القواعد. عطيني رقم الطالب الصحيح أو جرّب تطلب (ملخص/ساعات) أولًا."

            lines = []
            lines.append(f" هذه أفضل {len(rec)} مواد مقترحة لك (حسب وضعك الحالي):")
            for i, c in enumerate(rec, start=1):
                cid = c.get("course_id")
                name = c.get("course_name_ar") or c.get("course_name_en")
                cr = c.get("credits")
                reason = c.get("reason", "")
                lines.append(f"{i}) {cid} — {name} ({cr} ساعات)  {reason}")

            max_credits = rules.get("recommended_max_credits")
            if max_credits:
                lines.append(f"\n ملاحظة: الحد المقترح للساعات هذا الفصل = {max_credits}")

            return "\n".join(lines)

        if intent == "credits_summary":
            completed = data.get("completed", {})
            remaining = data.get("remaining", {})
            totals = data.get("totals", {})
            return (
                " ملخص الساعات:\n"
                f"- مكتملة: {completed.get('total', 0)} (إجباري: {completed.get('required', 0)} | اختياري: {completed.get('elective', 0)})\n"
                f"- متبقية: {remaining.get('total', 0)} (اختياري متبقي: {remaining.get('elective', 0)})\n"
                f"- إجمالي الخطة: {totals.get('program_total_credits', 0)} | اختياري مطلوب: {totals.get('program_major_elective_credits', 0)}"
            )

        if intent == "gpa_summary":
            off = data.get("official", {})
            term = off.get("term_gpa", {})
            cum = off.get("cumulative_gpa", {})
            return (
                " ملخص المعدل:\n"
                f"- المعدل الفصلي (4): {term.get('term_gpa_4', 0)} | (100): {term.get('term_gpa_100', 0)}\n"
                f"- المعدل التراكمي (4): {cum.get('cumulative_gpa_4', 0)} | (100): {cum.get('cumulative_gpa_100', 0)}"
            )

        if intent == "gpa_simulate":
            expected = data.get("expected", {})
            delta = data.get("delta", {})
            details = data.get("details", [])

            lines = []
            lines.append(" نتيجة محاكاة المعدل:")
            lines.append(f"- المعدل الفصلي المتوقع (4): {expected.get('term_gpa_4', 0)}")
            lines.append(f"- المعدل التراكمي المتوقع (4): {expected.get('cumulative_gpa_4', 0)}")
            lines.append(f"- التغير على التراكمي: {delta.get('cumulative_gpa_4_change', 0)}")

            if details:
                lines.append("\nتفاصيل المواد:")
                for d in details:
                    lines.append(f"- {d.get('course_id')} ({d.get('credits')} ساعات): {d.get('expected_grade')} → نقاط {d.get('expected_grade_points')}")

            return "\n".join(lines)

        if intent == "snapshot":
            st = data.get("student", {})
            prog = data.get("program", {})
            return (
                " ملخص وضعك الأكاديمي:\n"
                f"- الاسم: {st.get('name_ar','')}\n"
                f"- التخصص: {prog.get('program_name','')} (ID: {st.get('program_id')})\n"
                f"- المستوى: {st.get('level')}\n"
                f"- الساعات المكتملة: {st.get('completed_credits_computed', st.get('completed_credits'))}\n"
                f"- المعدل التراكمي: {st.get('cumulative_gpa_4', st.get('gpa'))}\n"
                f"- الفصل الحالي: {st.get('current_semester')}"
            )

        if intent == "knowledge_base_query":
            return "تمت معالجة السؤال عبر قاعدة المعرفة."

        return "تمام. اكتب سؤالك بشكل أوضح: (أهلية مقرر / توصيات / ساعات / معدل)."

    return "Done."