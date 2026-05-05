from typing import Dict, Any, List


def format_kb_reply(intent: str, api_results: List[Dict[str, Any]], language: str = "ar") -> str:
    ar = (language or "ar").lower().startswith("ar")

    if not api_results:
        return "لم أتمكن من الوصول إلى قاعدة المعرفة الآن." if ar else "I could not access the knowledge base."

    main = api_results[0]

    if not main.get("ok"):
        if ar:
            return "صار عندي مشكلة بسيطة أثناء جلب الإجابة من قاعدة المعرفة. جرّب مرة ثانية."
        return "I had a small issue while getting the answer from the knowledge base."

    response = main.get("response", {})
    data = response.get("data", {}) if isinstance(response, dict) else {}

    answer = data.get("answer", "")
    sources = data.get("sources", [])
    mode = data.get("mode", "")
    retrieved_count = data.get("retrieved_count", 0)

    if not answer:
        return "لم أجد إجابة واضحة في اللائحة المسترجعة." if ar else "I could not find a clear answer in the retrieved regulation."

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