"""POTA Content OS - Local Web Dashboard Server.

Khởi chạy máy chủ HTTP phục vụ giao diện Visual Control Board (`ui/`)
kết nối trực tiếp với LangGraph Cyclic StateGraph qua REST API:
- Phục vụ tĩnh: http://localhost:8080
- API Endpoints:
  + POST /api/start: Khởi chạy đồ thị với chủ đề do người dùng nhập
  + POST /api/touchpoint/resume: Nạp quyết định duyệt tại Touchpoint 1, 2, 3
  + GET /api/state: Lấy trạng thái State hiện tại của phiên
"""

import os
import sys
import json
import time
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any

from langgraph.types import Command
from core.state import ContentOSState
from graph.workflow import create_content_os_graph

PORT = 8080
UI_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui")

# Runtime Global State
app_graph = None
current_config = {"configurable": {"thread_id": "web_session_01"}}
latest_snapshot = None


def get_graph_app():
    global app_graph
    if app_graph is None:
        app_graph = create_content_os_graph()
    return app_graph


class ContentOSHTTPHandler(BaseHTTPRequestHandler):
    """Xử lý HTTP requests cho Web UI và API."""

    def _send_json(self, data: Dict[str, Any], status: int = 200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        global latest_snapshot, current_config
        app = get_graph_app()

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8")) if body else {}

        if self.path == "/api/start":
            focus_topic = payload.get("focus_topic", "").strip()
            thread_id = f"web_session_{int(time.time())}"
            current_config = {"configurable": {"thread_id": thread_id}}

            initial_state: ContentOSState = {
                "week_id": f"2026-W{time.strftime('%U')}",
                "brand_rules": [
                    "Brand Voice: Thực chiến, tốc độ, giải quyết triệt để bài toán kinh doanh",
                ],
                "trends_feed": [],
                "content_plan": [],
                "plan_approved": False,
                "selected_topic": {
                    "id": "seed_topic",
                    "angle": focus_topic or "Agentic AI Automation",
                    "hook_concept": f"Ý tưởng cho {focus_topic}",
                    "target_channel": "Facebook",
                    "core_message": focus_topic or "Tự động hóa đa kênh",
                } if focus_topic else {},
                "outline": {},
                "raw_draft": "",
                "draft_score": 0,
                "draft_feedback": "",
                "text_revision_count": 0,
                "fact_checked_draft": "",
                "threads_posts": [],
                "carousel_slides": [],
                "video_script": {},
                "raw_footage_url": None,
                "rendered_video_url": None,
                "video_duration": 0,
                "video_approved": False,
                "video_revision_count": 0,
                "cover_image_url": None,
                "image_approved": False,
                "image_revision_count": 0,
                "final_package_approved": False,
                "user_revision_note": None,
                "total_cycle_count": 0,
                "published_links": {},
                "weekly_metrics": {},
            }

            app.invoke(initial_state, config=current_config)
            latest_snapshot = app.get_state(current_config)

            self._send_json({
                "status": "STARTED",
                "next": latest_snapshot.next,
                "values": latest_snapshot.values,
            })

        elif self.path == "/api/touchpoint/resume":
            resume_data = payload.get("resume", {})
            app.invoke(Command(resume=resume_data), config=current_config)
            latest_snapshot = app.get_state(current_config)

            self._send_json({
                "status": "RESUMED",
                "next": latest_snapshot.next,
                "values": latest_snapshot.values,
            })
        else:
            self.send_error(404, "Endpoint not found")

    def do_GET(self):
        global latest_snapshot
        if self.path == "/api/state":
            app = get_graph_app()
            snap = app.get_state(current_config) if current_config else None
            self._send_json({
                "next": snap.next if snap else [],
                "values": snap.values if snap else {},
            })
            return

        # Phục vụ file tĩnh trong ui/
        req_path = self.path.split("?")[0]
        if req_path in ("/", ""):
            req_path = "/index.html"

        file_path = os.path.normpath(os.path.join(UI_DIR, req_path.lstrip("/")))

        # Ngăn chặn Directory Traversal
        if not file_path.startswith(UI_DIR) or not os.path.exists(file_path):
            self.send_error(404, f"File Not Found: {req_path}")
            return

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def start_server(port: int = PORT):
    server = ThreadingHTTPServer(("0.0.0.0", port), ContentOSHTTPHandler)
    print(f"\n=======================================================")
    print(f"🚀 POTA Content OS Web Dashboard is RUNNING!")
    print(f"🔗 Mở trình duyệt xem giao diện tại: http://localhost:{port}")
    print(f"=======================================================\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nĐã dừng máy chủ POTA Content OS.")
        server.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    start_server(port_arg)
