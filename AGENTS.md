# ANTIGRAVITY IDE RULES FOR CONTENT_OS PROJECT

## CODING STANDARDS & RESTRICTIONS:
1. **Never write monolithic files:** Mọi Agent phải nằm trong file riêng biệt thuộc thư mục `agents/`. Graph assembly bắt buộc nằm trong thư mục `graph/`.
2. **Strict Typing:** Luôn dùng `typing` (`TypedDict`, `Optional`, `List`, `Dict`, `Any`) và Pydantic V2 cho tất cả dữ liệu có cấu trúc.
3. **LangGraph Convention:** 
   - Tuyệt đối dùng cú pháp LangGraph 0.2+ hiện đại (sử dụng `from langgraph.types import interrupt, Command`).
   - Mọi hàm Node chỉ nhận tham số `state: ContentOSState` và trả về dictionary cập nhật từng phần của state.
4. **Structured LLM Output:** 
   - Với Agent chấm điểm (`review_agent`), Agent kịch bản (`script_agent`), và Agent lập plan (`planner_agent`), bắt buộc sử dụng phương thức `.with_structured_output(PydanticModel)` để đảm bảo đầu ra luôn là JSON có cấu trúc chuẩn xác.
5. **No Hallucinated Tools:** Không tự chế các module mock không kiểm soát. Đối với các tác vụ dựng video hoặc cào dữ liệu, tạo interface rõ ràng với Type Hint để dễ dàng tích hợp API thật (như Ayrshare, HeyGen, CapCut API) sau này.

## TASK EXECUTION ROADMAP:
Khi người dùng yêu cầu triển khai, AI Agent trong IDE phải thực hiện tuần tự theo các phase:
- **Phase 1:** Hoàn thiện `core/state.py` và `config.py` kèm unit test state.
- **Phase 2:** Xây dựng `agents/planning/` và `graph/` để chạy thử Chặng 1 kèm điểm ngắt `interrupt()` đầu tiên.
- **Phase 3:** Xây dựng `agents/text_pipeline/` và khép kín vòng lặp tự sửa bài (Chấm điểm < 8đ viết lại).
- **Phase 4:** Xây dựng `agents/media_pipeline/` và Node hội tụ dữ liệu.
- **Phase 5:** Tích hợp `operations/` (Xuất bản, Bình luận, Phân tích tuần) và hoàn thiện `main.py` CLI tương tác hoàn chỉnh.
