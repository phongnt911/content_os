"""LinTech Content OS - Interactive CLI Runner.

CLI tương tác điều khiển chu trình sản xuất và phân phối nội dung tự động:
- Khởi chạy Cyclic StateGraph & DAG Fork-Join với Checkpointer bộ nhớ.
- Dừng tương tác tại 3 Human Touchpoints:
  + Touchpoint 1: Duyệt Kế hoạch tuần (Plan Approval)
  + Touchpoint 2: Nhận link Video Footage thô từ Creator
  + Touchpoint 3: Duyệt trọn gói bộ ấn phẩm (Text, Threads, Carousel, Video, Cover)
- Tự động xuất bản đa kênh, xây dựng kịch bản bình luận và học máy cập nhật Brand Rules.
"""

import sys
import time
from typing import Dict, Any
from langgraph.types import Command
from core.state import ContentOSState
from graph.workflow import create_content_os_graph


BANNER = r"""
================================================================================
   _     _       _____           _        ____            _             _       ___  ____  
  | |   (_)_ __ |_   _|__  ___| |__    / ___|___  _ __ | |_ ___ _ __ | |_   / _ \/ ___| 
  | |   | | '_ \  | |/ _ \/ __| '_ \  | |   / _ \| '_ \| __/ _ \ '_ \| __| | | | \___ \ 
  | |___| | | | | | |  __/ (__| | | | | |__| (_) | | | | ||  __/ | | | |_  | |_| |___) |
  |_____|_|_| |_| |_|\___|\___|_| |_|  \____\___/|_| |_|\__\___|_| |_|\__|  \___/|____/ 
                                                                                        
         -- Autonomous Multi-Agent Content Production & Distribution System --
================================================================================
"""


def print_divider(title: str = "") -> None:
    if title:
        print(f"\n{'-' * 25} [ {title} ] {'-' * 25}")
    else:
        print("-" * 70)


def prompt_touchpoint_1(interrupt_data: Dict[str, Any]) -> Command:
    """Tương tác Human Touchpoint 1: Phê duyệt ma trận kế hoạch tuần."""
    print_divider("HUMAN TOUCHPOINT 1: DUYỆT KẾ HOẠCH TUẦN")
    content_plan = interrupt_data.get("content_plan", [])
    print(f"Ma trận kế hoạch tuần ({len(content_plan)} bài viết):")
    for idx, item in enumerate(content_plan, 1):
        print(f"  {idx}. [{item.get('target_channel', 'Facebook')}] ID: {item.get('id')}")
        print(f"     Angle: {item.get('angle')}")
        print(f"     Hook:  {item.get('hook_concept')}")
        print(f"     Core:  {item.get('core_message')}")
        print()

    print("Quyết định của bạn:")
    print("  [Y] Duyệt kế hoạch (Kích hoạt Dây chuyền Chữ & Dây chuyền Media song song)")
    print("  [N] Từ chối kế hoạch (Kết thúc chu trình)")

    try:
        choice = input("Lựa chọn (Y/N, mặc định Y): ").strip().lower()
    except EOFError:
        choice = "y"

    if choice in ("n", "no"):
        try:
            note = input("Lý do từ chối: ").strip()
        except EOFError:
            note = "Chủ đề chưa sát mục tiêu"
        print("[!] Đã từ chối kế hoạch. Luồng sẽ kết thúc.")
        return Command(resume={"approved": False, "note": note or "User rejected plan"})

    print("[OK] Kế hoạch đã được phê duyệt! Bắt đầu phân nhánh song song...")
    return Command(resume={"approved": True, "note": "Phê duyệt kế hoạch tuần"})


def prompt_touchpoint_2(interrupt_data: Dict[str, Any]) -> Command:
    """Tương tác Human Touchpoint 2: Nhận link video raw từ Creator."""
    print_divider("HUMAN TOUCHPOINT 2: QUAY VIDEO RAW")
    script = interrupt_data.get("video_script", {})
    print("Kịch bản video đã được Agent 9 soạn thảo:")
    print(f"  Thời lượng ước tính: {script.get('total_estimated_duration', 45)}s")
    print(f"  Hook mở đầu (3s):    \"{script.get('hook_opening', '')}\"")
    print("  Các phân cảnh:")
    for scene in script.get("scenes", []):
        print(f"    - Cảnh {scene.get('scene_number')} ({scene.get('duration_seconds')}s):")
        print(f"      Visual:   {scene.get('visual_cue')}")
        print(f"      Prompter: \"{scene.get('voice_prompter')}\"")
    print(f"  CTA kết video:       \"{script.get('cta_closing', '')}\"")
    print()

    print("Hướng dẫn: Creator vui lòng đọc kịch bản, quay clip và dán link Google Drive video thô.")
    try:
        url_input = input("Nhập URL Video thô (Nhấn Enter để dùng video mẫu demo): ").strip()
    except EOFError:
        url_input = ""

    default_url = "https://drive.google.com/file/d/creator_raw_footage_1080p/view"
    chosen_url = url_input if url_input else default_url
    print(f"[OK] Đã tiếp nhận video: {chosen_url}")
    print("[*] Agent 10 đang cắt dựng, ghép sub và B-roll...")
    return Command(resume={"raw_footage_url": chosen_url})


def prompt_touchpoint_3(interrupt_data: Dict[str, Any]) -> Command:
    """Tương tác Human Touchpoint 3: Phê duyệt trọn gói Final Package."""
    print_divider("HUMAN TOUCHPOINT 3: DUYỆT TRỌN GÓI NỘI DUNG (FINAL PACKAGE)")
    print(f"Chu kỳ duyệt hiện tại: {interrupt_data.get('cycle_count')}/{interrupt_data.get('max_cycles_allowed')}")
    print("\n--- 1. BÀI VIẾT FACEBOOK ---")
    draft = interrupt_data.get("text_draft", "")
    print(draft[:400] + ("..." if len(draft) > 400 else ""))

    print(f"\n--- 2. CHUỖI BÀI THREADS ({len(interrupt_data.get('threads_posts', []))} POSTS) ---")
    for p in interrupt_data.get("threads_posts", [])[:3]:
        print(f"  - {p}")

    print(f"\n--- 3. BỘ SLIDE CAROUSEL: {interrupt_data.get('carousel_slides_count')} trang ---")
    print(f"--- 4. VIDEO RENDER: {interrupt_data.get('rendered_video_url')} ({interrupt_data.get('video_duration_seconds')}s) ---")
    print(f"--- 5. THUMBNAIL COVER: {interrupt_data.get('cover_image_url')} ---")

    print("\nQuyết định của bạn:")
    print("  [Y] Phê duyệt xuất bản ngay (Kích hoạt Agent 14, 15, 16)")
    print("  [R] Yêu cầu chỉnh sửa lại")

    try:
        choice = input("Lựa chọn (Y/R, mặc định Y): ").strip().lower()
    except EOFError:
        choice = "y"

    if choice in ("r", "revise"):
        try:
            note = input("Góp ý chỉnh sửa (nội dung hoặc video): ").strip()
        except EOFError:
            note = "Sửa lại mở bài cho giật tò mò hơn"
        return Command(resume={"approved": False, "note": note or "Chỉnh sửa lại nội dung"})

    print("[OK] Đã duyệt trọn bộ gói ấn phẩm! Bắt đầu bắn API xuất bản đa kênh...")
    return Command(resume={"approved": True})


def run_interactive_content_os(auto_approve: bool = False) -> None:
    """Chạy toàn bộ chu trình LinTech Content OS với tương tác dòng lệnh."""
    print(BANNER)
    print("Đang khởi tạo LinTech Content OS Cyclic StateGraph...")

    app = create_content_os_graph()
    thread_id = f"content_os_session_{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: ContentOSState = {
        "week_id": f"2026-W{time.strftime('%U')}",
        "brand_rules": [
            "Brand Voice: Thực chiến, tốc độ, giải quyết triệt để bài toán kinh doanh",
            "Mỗi bài viết phải giải phóng thời gian cho solopreneur và tech team",
        ],
        "trends_feed": [],
        "content_plan": [],
        "plan_approved": False,
        "selected_topic": {},
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

    print(f"Bắt đầu chu trình cho Tuần: {initial_state['week_id']}")
    print("[*] Agent 1 (Research) đang quét tin tức và radar đối thủ...")
    print("[*] Agent 2 (Plan) đang lập ma trận nội dung tuần...")

    # Khởi chạy đồ thị lần đầu
    app.invoke(initial_state, config=config)

    # Vòng lặp lắng nghe các điểm ngắt interrupt()
    while True:
        state_snapshot = app.get_state(config)
        next_nodes = state_snapshot.next

        if not next_nodes:
            print("\n[V] Đồ thị đã hoàn thành tất cả các bước (END).")
            break

        tasks = state_snapshot.tasks or []
        interrupt_value = None
        for task in tasks:
            if task.interrupts:
                interrupt_value = task.interrupts[0].value
                break

        if not interrupt_value:
            break

        touchpoint = interrupt_value.get("touchpoint")

        if touchpoint == 1:
            if auto_approve:
                resume_cmd = Command(resume={"approved": True, "note": "Auto-approved"})
            else:
                resume_cmd = prompt_touchpoint_1(interrupt_value)
            app.invoke(resume_cmd, config=config)

        elif touchpoint == 2:
            if auto_approve:
                resume_cmd = Command(resume={"raw_footage_url": "https://drive.google.com/sample_auto.mp4"})
            else:
                resume_cmd = prompt_touchpoint_2(interrupt_value)
            app.invoke(resume_cmd, config=config)

        elif touchpoint == 3:
            if auto_approve:
                resume_cmd = Command(resume={"approved": True})
            else:
                resume_cmd = prompt_touchpoint_3(interrupt_value)
            app.invoke(resume_cmd, config=config)

        else:
            print(f"[!] Điểm ngắt không xác định: {interrupt_value}")
            break

    # Lấy state sau cùng
    final_snapshot = app.get_state(config)
    final_values = final_snapshot.values

    print_divider("BÁO CÁO KẾT THÚC CHU TRÌNH")
    if final_values.get("published_links"):
        print("[+] Các liên kết bài đăng đã xuất bản:")
        for platform, url in final_values["published_links"].items():
            print(f"    - {platform.capitalize():15}: {url}")

    if final_values.get("weekly_metrics"):
        print("\n[+] Báo cáo hiệu quả & đo lường tuần (Agent 16):")
        metrics = final_values["weekly_metrics"].get("metrics_summary", {})
        for metric_name, val in metrics.items():
            print(f"    - {metric_name:22}: {val}")

    print("\n[+] Bộ quy tắc thương hiệu đã được bổ sung bài học mới:")
    for rule in final_values.get("brand_rules", []):
        print(f"    * {rule}")

    print("\n[SUCCESS] LinTech Content OS đã thực thi xuất sắc toàn bộ quy trình 16 Agents!")


if __name__ == "__main__":
    is_auto = "--auto" in sys.argv
    run_interactive_content_os(auto_approve=is_auto)
