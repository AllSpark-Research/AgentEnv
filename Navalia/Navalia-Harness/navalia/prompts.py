from pathlib import Path

SYSTEM_PROMPT = (Path(__file__).resolve().parents[1] / "conf" / "system.txt").read_text()


def build_user_prompt(question: str, source_files: list[str] | None = None) -> str:
    lines: list[str] = []
    lines.append("Answer the following question using the documents in /workspace/corpus/transformed/.")
    lines.append("")
    lines.append(f"Question: {question}")
    if source_files:
        lines.append("")
        lines.append("Documents that have been mounted into /workspace/corpus/transformed/ for you:")
        for sf in source_files:
            lines.append(f"  - {sf}")
    lines.append("")
    lines.append(
        "Remember: end your final assistant message with the two XML blocks <REASONING>...</REASONING> and <FINAL_ANSWER>...</FINAL_ANSWER>, in that order."
    )
    return "\n".join(lines)
