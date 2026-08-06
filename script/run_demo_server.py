from __future__ import annotations

from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from typing import Any

HOST = "127.0.0.1"
PORT = 8010
MAX_REQUEST_BYTES = 16_384


class AgentRuntime:
    def __init__(self) -> None:
        self._agent: Any | None = None
        self._lock = threading.Lock()

    def ask(self, question: str) -> str:
        with self._lock:
            from core.config import load_settings
            from retrieval.agent import build_agent, run_agent_question
            from retrieval.index import LocalEmbeddingIndex

            if self._agent is None:
                settings = load_settings()
                index = LocalEmbeddingIndex.load(settings, settings.paths.embeddings_json)
                self._agent = build_agent(settings=settings, index=index)
            return run_agent_question(self._agent, question)


runtime = AgentRuntime()


class DemoHandler(SimpleHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/api/agent":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > MAX_REQUEST_BYTES:
                raise ValueError("Kich thuoc yeu cau khong hop le.")
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            question = str(payload.get("question", "")).strip()
            if not question:
                raise ValueError("Cau hoi khong duoc de trong.")
            if len(question) > 1_000:
                raise ValueError("Cau hoi khong duoc vuot qua 1.000 ky tu.")
            answer = runtime.ask(question)
            self._send_json(200, {"question": question, "answer": answer})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": f"Agent khong the tra loi: {exc}"})

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    handler = lambda *args, **kwargs: DemoHandler(*args, directory=str(project_dir), **kwargs)
    server = ThreadingHTTPServer((HOST, PORT), handler)
    print(f"Demo dashboard: http://{HOST}:{PORT}/demo-pipeline-dashboard.html")
    print("Nhan Ctrl+C de dung server.")
    server.serve_forever()


if __name__ == "__main__":
    main()
