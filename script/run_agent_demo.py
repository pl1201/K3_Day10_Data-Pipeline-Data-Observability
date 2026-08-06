from __future__ import annotations

from core.config import load_settings
from core.utils import write_json
from retrieval.agent import build_agent, run_agent_question
from retrieval.index import LocalEmbeddingIndex


DEMO_QUESTIONS = [
    "Agentic Retrieval-Augmented Generation là gì? Hãy trả lời bằng tiếng Việt.",
    "Hãy liệt kê tác giả của bài báo mới nhất trong kho dữ liệu và trả lời bằng tiếng Việt.",
    "Các bài báo về mô hình ngôn ngữ lớn trong kho dữ liệu thuộc những chủ đề nào? Hãy trả lời bằng tiếng Việt.",
]


def main() -> None:
    settings = load_settings()
    index = LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json)
    agent = build_agent(settings=settings, index=index)

    answers = []
    for number, question in enumerate(DEMO_QUESTIONS, start=1):
        print(f"[{number}/{len(DEMO_QUESTIONS)}] {question}")
        answer = run_agent_question(agent, question)
        answers.append({"question": question, "answer": answer})
        print(f"    {answer}\n")

    write_json(settings.paths.demo_answers, answers)
    print(f"Agent demo saved to {settings.paths.demo_answers}")


if __name__ == "__main__":
    main()
