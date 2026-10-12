"""LangGraph Edge Routing & Conditional Edges.

Định nghĩa các hàm điều kiện rẽ nhánh và vòng lặp theo đặc tả:
- route_after_plan_approval: Rẽ nhánh sau Human Touchpoint 1
"""

from typing import Literal
from langgraph.graph import END
from core.state import ContentOSState


def route_after_plan_approval(state: ContentOSState) -> str:
    """Conditional Edge sau Human Touchpoint 1.
    
    Quy tắc:
    - Nếu plan_approved == True: Đi tiếp vào `plan_dispatch` (sẵn sàng fork song song Chặng 2).
    - Nếu plan_approved == False: Kết thúc luồng (END).
    """
    if state.get("plan_approved", False):
        return "plan_dispatch"
    return END
