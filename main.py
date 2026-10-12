"""POTA Content OS - Interactive CLI Runner.

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

# Thiết lập encoding UTF-8 cho console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


BANNER = r"""
================================================================================
   ____   ___ _____  _      ____ ___  _   _ _____ _____ _   _ _____    ___  ____  
  |  _ \ / _ \_   _|/ \    / ___/ _ \| \ | |_   _| ____| \ | |_   _|  / _ \/ ___| 
  | |_) | | | || | / _ \  | |  | | | |  \| | | | |  _| |  \| | | |   | | | \___ \ 
  |  __/| |_| || |/ ___ \ | |__| |_| | |\  | | | | |___| |\  | | |   | |_| |___) |
  |_|    \___/ |_/_/   \_\ \____\___/|_| \_| |_| |_____|_| \_| |_|    \___/|____/ 
                                                                                
         -- Autonomous Multi-Agent Content Production & Distribution System --
================================================================================
"""


def print_divider(title: str = "") -> None:
    if title:
        print(f"\n{'-' * 25} [ {title} ] {'-' * 25}")
    else:
        print("-" * 70)


def prompt_touchpoint_1(interrupt_data: Dict[str, Any]) -> Command:
    """Tương tác Human Touchpoint 1: Phê duyệt ma trận kế hoạch tuần và chọn chủ đề."""
    print_divider("HUMAN TOUCHPOINT 1: DUYỆT KẾ HOẠCH TUẦN & CHỌN CHỦ ĐỀ")
    content_plan = interrupt_data.get("content_plan", [])
    total_posts = len(content_plan)
    print(f"Ma trận kế hoạch tuần ({total_posts} bài viết):")
    for idx, item in enumerate(content_plan, 1):
        print(f"  [{idx}] [{item.get('target_channel', 'Facebook')}] ID: {item.get('id')}")
        print(f"      Góc tiếp cận: {item.get('angle')}")
        print(f"      Ý tưởng Hook: {item.get('hook_concept')}")
        print(f"      Thông điệp:   {item.get('core_message')}")
        print()

    print("Quyết định của bạn:")
    print(f"  [1 - {total_posts}] Chọn bài viết tương ứng để sản xuất video & nội dung ngay")
    print("  [Y]     Duyệt toàn bộ và lấy bài số 1 mặc định")
    print("  [C]     Nhập chủ đề tùy chỉnh mới hoàn toàn (Custom Topic)")
    print("  [N]     Từ chối kế hoạch (Chuyển đổi hướng hoặc dừng luồng)")

    try:
        raw_choice = input(f"Lựa chọn (1-{total_posts} / Y / C / N, mặc định 1): ").strip()
    except EOFError:
        raw_choice = "1"

    choice = raw_choice.lower()

    if choice in ("n", "no"):
        try:
            print("\nBạn chưa ưng ý các bài viết trên?")
            new_direction = input("Nhập chủ đề hoặc góc tiếp cận bạn muốn hướng tới (hoặc nhấn Enter để dừng luồng): ").strip()
        except EOFError:
            new_direction = ""

        if new_direction:
            print(f"[OK] Đã tiếp nhận định hướng mới: '{new_direction}'. POTA sẽ chuyển hướng sản xuất theo chủ đề này!")
            return Command(resume={"approved": True, "custom_topic": new_direction, "note": f"User topic pivot: {new_direction}"})
        else:
            print("[!] Đã dừng luồng theo yêu cầu.")
            return Command(resume={"approved": False, "note": "User rejected plan and stopped workflow"})

    if choice == "c":
        try:
            custom_title = input("Nhập chủ đề / góc bài viết tùy chỉnh của bạn: ").strip()
        except EOFError:
            custom_title = "Chủ đề tự chọn theo yêu cầu"
        print(f"[OK] Đã chọn chủ đề tùy chỉnh: '{custom_title}'")
        return Command(resume={"approved": True, "custom_topic": custom_title})

    # Nếu người dùng nhập số thứ tự bài
    if choice.isdigit():
        idx = int(choice)
        if 1 <= idx <= total_posts:
            chosen_post = content_plan[idx - 1]
            print(f"[OK] Đã chọn bài số {idx}: '{chosen_post.get('angle')}'")
            return Command(resume={"approved": True, "selected_index": idx - 1})

    # Mặc định chọn bài 1
    default_post = content_plan[0] if content_plan else {}
    print(f"[OK] Đã chọn bài số 1: '{default_post.get('angle', 'N/A')}'")
    return Command(resume={"approved": True, "selected_index": 0})


def prompt_touchpoint_2(interrupt_data: Dict[str, Any]) -> Command:
    """Tương tác Human Touchpoint 2: Nhận link video thô sau khi Creator quay xong."""
    print_divider("HUMAN TOUCHPOINT 2: NẠP VIDEO FOOTAGE THÔ (CREATOR ACTION)")
    video_script = interrupt_data.get("video_script", {})
    hook = interrupt_data.get("hook_opening", "")
    scenes = video_script.get("scenes", [])
    cta = video_script.get("cta_closing", "")

    print(f"Hook mở đầu 3s: \"{hook}\"")
    print(f"Tổng số phân cảnh: {len(scenes)}")
    for s in scenes:
        print(f"  [Cảnh {s.get('scene_number', '?')}] ({s.get('duration_seconds', 0)}s):")
        print(f"    - Visual: {s.get('visual_cue')}")
        print(f"    - Voice:  \"{s.get('voice_prompter')}\"")
    print(f"CTA kết: \"{cta}\"\n")

    print("[*] Vui lòng quay video theo kịch bản trên và tải lên Google Drive / Server.")
    try:
        raw_url = input("Dán URL video thô (nhấn Enter để dùng link mẫu demo): ").strip()
    except EOFError:
        raw_url = ""

    footage_url = raw_url if raw_url else "https://drive.google.com/file/d/sample_footage_creator_1080p/view"
    print(f"[OK] Đã nhận video footage: {footage_url}")
    return Command(resume={"raw_footage_url": footage_url})


def prompt_touchpoint_3(interrupt_data: Dict[str, Any]) -> Command:
    """Tương tác Human Touchpoint 3: Phê duyệt trọn bộ gói ấn phẩm trước khi xuất bản."""
    print_divider("HUMAN TOUCHPOINT 3: PHÊ DUYỆT TRỌN BỘ ẤN PHẨM TRƯỚC XUẤT BẢN")
    pkg = interrupt_data.get("package", {})

    print(f"[1] Bài viết Facebook (Score: {pkg.get('draft_score')}/10):")
    draft_preview = pkg.get("article_draft", "")
    print(f"    {draft_preview[:300]}...\n")

    threads = pkg.get("threads_posts", [])
    print(f"[2] Chuỗi bài Threads ({len(threads)} posts):")
    for idx, tp in enumerate(threads[:2], 1):
        print(f"    Post {idx}: {tp}")
    if len(threads) > 2:
        print(f"    ... và {len(threads) - 2} post khác.")
    print()

    slides = pkg.get("carousel_slides", [])
    print(f"[3] Kịch bản Carousel ({len(slides)} slides):")
    for idx, sl in enumerate(slides[:2], 1):
        print(f"    Slide {idx}: {sl.get('headline')} | Visual: {sl.get('visual_layout_tip')}")
    print()

    print(f"[4] Video ngắn đã dựng: {pkg.get('rendered_video_url')} ({pkg.get('video_duration')}s)")
    print(f"[5] Ảnh bìa Thumbnail:   {pkg.get('cover_image_url')}\n")

    print("Quyết định phê duyệt:")
    print("  [Y] Duyệt trọn gói & Bắt đầu Xuất bản đa kênh ngay")
    print("  [R] Yêu cầu chỉnh sửa lại (Kèm ghi chú phản hồi)")

    try:
        choice = input("Lựa chọn (Y/R, mặc định Y): ").strip().lower()
    except EOFError:
        choice = "y"

    if choice == "r":
        try:
            note = input("Nhập ghi chú yêu cầu chỉnh sửa: ").strip()
        except EOFError:
            note = "Cần tinh chỉnh lại hook cho hấp dẫn hơn"
        print(f"[!] Yêu cầu chỉnh sửa: '{note}'. Đồ thị sẽ quay lại bước cải thiện...")
        return Command(resume={"approved": False, "note": note})

    print("[OK] Đã phê duyệt trọn gói! Bắt đầu phát hành tự động đa nền tảng...")
    return Command(resume={"approved": True})


def run_interactive_content_os(auto_approve: bool = False) -> None:
    """Chạy toàn bộ chu trình POTA Content OS với tương tác dòng lệnh."""
    print(BANNER)
    print("Đang khởi tạo POTA Content OS Cyclic StateGraph...")

    app = create_content_os_graph()
    thread_id = f"content_os_session_{int(time.time())}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state: ContentOSState = {
        "week_id": f"2026-W{time.strftime('%U')}",
        "brand_rules": [
            "Brand Voice: Thực chiến, tốc độ, giải quyết triệt để bài toán kinh doanh",
            "Mỗi bài viết phải giải phóng thời gian và gia tăng giá trị cho độc giả",
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

    if not auto_approve:
        print_divider("KHỞI TẠO CHỦ ĐỀ TUẦN")
        try:
            user_topic_seed = input("Nhập chủ đề trọng tâm tuần này (Nhấn Enter để AI tự động quét radar xu hướng): ").strip()
            if user_topic_seed:
                initial_state["selected_topic"] = {
                    "id": "seed_topic",
                    "angle": user_topic_seed,
                    "hook_concept": f"Ý tưởng mở bài cho: {user_topic_seed}",
                    "target_channel": "Đa kênh",
                    "core_message": user_topic_seed,
                }
                print(f"[OK] Đã thiết lập chủ đề trọng tâm: '{user_topic_seed}'")
            else:
                print("[*] Không nhập chủ đề riêng -> AI sẽ tự động quét radar đa ngành...")
        except EOFError:
            pass

    print(f"\nBắt đầu chu trình cho Tuần: {initial_state['week_id']}")
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

    if final_values.get("brand_rules"):
        print("\n[+] Bộ quy tắc thương hiệu đã được bổ sung bài học mới:")
        for rule in final_values.get("brand_rules", []):
            print(f"    * {rule}")

    print("\n[SUCCESS] POTA Content OS đã thực thi xuất sắc chu trình sản xuất nội dung!")


if __name__ == "__main__":
    is_auto = "--auto" in sys.argv
    run_interactive_content_os(auto_approve=is_auto)
