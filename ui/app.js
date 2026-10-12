/**
 * PoTa Content OS - Visual Workflow Controller (app.js)
 * Điều khiển trạng thái thời gian thực của 16 Agents & 3 Human Touchpoints
 */

let workflowState = {
    isRunning: false,
    currentTouchpoint: null,
    activeAgentsCount: 0,
    planItems: [],
    selectedPlanIndex: 0,
    stateData: {}
};

// Map từ Node ID sang HTML Element ID
const NODE_ELEMENT_MAP = {
    "research": "node-research",
    "planner": "node-planner",
    "human_approve_plan": "node-touchpoint-1",
    "generate_outline": "node-outline",
    "writer": "node-writer",
    "review_text": "node-review-text",
    "fact_check": "node-factcheck",
    "repurpose_threads": "node-repurpose",
    "generate_carousel": "node-carousel",
    "generate_video_script": "node-script",
    "human_record_video": "node-touchpoint-2",
    "video_editing": "node-video-editor",
    "review_video": "node-review-video",
    "generate_cover_image": "node-cover",
    "review_image": "node-review-image",
    "human_approve_final_package": "node-touchpoint-3",
    "publisher": "node-publisher",
    "comment_manager": "node-community",
    "analytics_learner": "node-analytics"
};

// Ghi log vào Terminal
function logMessage(msg, type = "info") {
    const logsContainer = document.getElementById("terminalLogs");
    if (!logsContainer) return;

    const line = document.createElement("div");
    line.className = `log-line log-${type}`;
    const time = new Date().toLocaleTimeString();
    line.innerText = `[${time}] ${msg}`;
    logsContainer.appendChild(line);
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

function clearLogs() {
    const logsContainer = document.getElementById("terminalLogs");
    if (logsContainer) logsContainer.innerHTML = "";
}

function updateActiveCount(count) {
    workflowState.activeAgentsCount = count;
    const el = document.getElementById("activeCount");
    if (el) el.innerText = String(count).padStart(2, '0');
}

function setNodeRunning(nodeKey) {
    const elId = NODE_ELEMENT_MAP[nodeKey] || nodeKey;
    const el = document.getElementById(elId);
    if (el) {
        el.classList.add("node-running");
        el.classList.remove("node-done");
    }
}

function setNodeDone(nodeKey) {
    const elId = NODE_ELEMENT_MAP[nodeKey] || nodeKey;
    const el = document.getElementById(elId);
    if (el) {
        el.classList.remove("node-running");
        el.classList.add("node-done");
    }
}

// ==========================================================================
// KHỞI CHẠY QUY TRÌNH (API HOẶC CLIENT SIMULATION)
// ==========================================================================
async function handleStartWorkflow() {
    const topicInput = document.getElementById("topicInput").value.trim();
    const btn = document.getElementById("btnStartFlow");
    btn.disabled = true;
    btn.innerHTML = "<span>⏳ ĐANG CHẠY...</span>";

    logMessage(`Khởi chạy PoTa Content OS... Chủ đề: "${topicInput || 'Tự động quét radar'}"`, "system");

    // Thử gọi Backend API server nếu đang chạy
    try {
        const res = await fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ focus_topic: topicInput })
        });
        if (res.ok) {
            const data = await res.json();
            logMessage("Đã kết nối trực tiếp StateGraph Backend!", "success");
            pollWorkflowStatus();
            return;
        }
    } catch (e) {
        // Fallback: Chạy Client Simulation trực quan nếu mở file HTML trực tiếp
        logMessage("Chạy Visual Simulation Engine trực tiếp trên giao diện...", "info");
        runClientSimulation(topicInput);
    }
}

// ==========================================================================
// SIMULATION ENGINE CHO GIAO DIỆN TRỰC QUAN
// ==========================================================================
async function runClientSimulation(customTopic) {
    updateActiveCount(2);
    setNodeRunning("research");
    logMessage("[Agent 01: Research] Đang quét radar công nghệ & đối thủ...", "info");
    await sleep(1500);
    setNodeDone("research");

    setNodeRunning("planner");
    logMessage("[Agent 02: Planner] Đang thiết lập ma trận kế hoạch tuần 5-7 bài...", "info");
    await sleep(1500);
    setNodeDone("planner");

    updateActiveCount(0);
    // Dừng tại Touchpoint 1
    const defaultTopic = customTopic || "Tự động hóa sản xuất nội dung với Agentic AI";
    workflowState.planItems = [
        { id: "post_01", channel: "Facebook", angle: `Góc chiến lược: ${defaultTopic}`, hook: "Đừng làm content bằng tay nếu không muốn kiệt sức", core: "Tiết kiệm 80% thời gian với 16 Agents" },
        { id: "post_02", channel: "TikTok", angle: `Case Study: Triển khai ${defaultTopic} trong 3 ngày`, hook: "Tôi đã tự động hóa 90% content như thế nào?", core: "Quy trình từ ý tưởng đến video hoàn chỉnh" },
        { id: "post_03", channel: "Threads", angle: `Nghịch lý: Làm việc thông minh thay vì chăm chỉ`, hook: "99% creator đang mắc sai lầm này...", core: "Tối ưu chuỗi quy trình khép kín" },
        { id: "post_04", channel: "Shorts", angle: `Kỹ thuật Prompting chuẩn cấu trúc cho Agent`, hook: "Bí mật đằng sau các AI Agent triệu view", core: "Kiến trúc hệ thống tự hành" }
    ];

    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.add("waiting");
    logMessage("[TOUCHPOINT 1] Hệ thống tạm dừng chờ bạn phê duyệt Kế hoạch tuần!", "warn");
    openTouchpoint1Modal();
}

function openTouchpoint1Modal() {
    const list = document.getElementById("planCardsList");
    list.innerHTML = "";

    workflowState.planItems.forEach((item, idx) => {
        const card = document.createElement("div");
        card.className = `plan-item-card ${idx === workflowState.selectedPlanIndex ? 'selected' : ''}`;
        card.onclick = () => selectPlanCard(idx);
        card.innerHTML = `
            <div class="card-top">
                <span class="card-idx">Bài ${idx + 1} (${item.id})</span>
                <span class="card-channel">${item.channel}</span>
            </div>
            <div class="card-angle">${item.angle}</div>
            <div class="card-hook">Hook: "${item.hook}"</div>
        `;
        list.appendChild(card);
    });

    document.getElementById("modalTouchpoint1").classList.add("active");
}

function selectPlanCard(idx) {
    workflowState.selectedPlanIndex = idx;
    const cards = document.querySelectorAll(".plan-item-card");
    cards.forEach((c, i) => {
        if (i === idx) c.classList.add("selected");
        else c.classList.remove("selected");
    });
}

async function submitTouchpoint1(isApproved) {
    closeModal("modalTouchpoint1");
    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.remove("waiting");

    if (!isApproved) {
        logMessage("[Touchpoint 1] Bạn đã từ chối kế hoạch. Luồng kết thúc.", "warn");
        return;
    }

    const customVal = document.getElementById("customTopicInput").value.trim();
    const chosenPost = customVal ? { angle: customVal } : workflowState.planItems[workflowState.selectedPlanIndex];

    logMessage(`[Touchpoint 1] Phê duyệt thành công! Triển khai bài: "${chosenPost.angle}"`, "success");
    setNodeDone("node-touchpoint-1");

    // Rẽ nhánh song song 2 dây chuyền!
    updateActiveCount(2);
    runParallelPipelines(chosenPost);
}

async function runParallelPipelines(chosenTopic) {
    logMessage("[FORK] Đồ thị rẽ nhánh song song: Dây chuyền Chữ & Dây chuyền Video bắt đầu cùng lúc!", "system");

    // Nhánh Chữ: Dàn ý
    setNodeRunning("generate_outline");
    setNodeRunning("generate_video_script");
    await sleep(1400);
    setNodeDone("generate_outline");
    setNodeDone("generate_video_script");

    // Nhánh Video dừng tại Touchpoint 2
    const tp2El = document.getElementById("node-touchpoint-2");
    if (tp2El) tp2El.classList.add("waiting");
    logMessage("[TOUCHPOINT 2] Kịch bản video đã xong! Chờ Creator quay video raw...", "warn");

    // Trong khi đó nhánh chữ vẫn tiếp tục viết:
    setNodeRunning("writer");
    logMessage("[Agent 04: Writer] Đang chấp bút bài viết Facebook chuẩn Brand Voice...", "info");
    await sleep(1500);
    setNodeDone("writer");

    setNodeRunning("review_text");
    logMessage("[Agent 05: QA Review] Chấm điểm 9/10 (Đạt chuẩn). Cho phép đi tiếp...", "info");
    await sleep(1200);
    setNodeDone("review_text");

    setNodeRunning("fact_check");
    await sleep(1000);
    setNodeDone("fact_check");

    setNodeRunning("repurpose_threads");
    await sleep(1200);
    setNodeDone("repurpose_threads");

    setNodeRunning("generate_carousel");
    await sleep(1200);
    setNodeDone("generate_carousel");
    logMessage("[Nhánh Chữ] Đã hoàn thành dàn bài, Threads và Carousel. Sẵn sàng hội tụ!", "success");

    // Bật modal Touchpoint 2 để creator nạp clip
    openTouchpoint2Modal();
}

function openTouchpoint2Modal() {
    document.getElementById("modalTouchpoint2").classList.add("active");
}

async function submitTouchpoint2() {
    closeModal("modalTouchpoint2");
    const tp2El = document.getElementById("node-touchpoint-2");
    if (tp2El) tp2El.classList.remove("waiting");
    setNodeDone("node-touchpoint-2");

    const url = document.getElementById("rawFootageInput").value.trim();
    logMessage(`[Touchpoint 2] Đã nạp video thô: ${url}`, "success");

    // Chạy tiếp nhánh Video
    updateActiveCount(2);
    setNodeRunning("video_editing");
    logMessage("[Agent 10: Video Editor] Đang auto-cut, chèn sub động và B-roll...", "info");
    await sleep(1600);
    setNodeDone("video_editing");

    setNodeRunning("review_video");
    logMessage("[Agent 11: Review Video] Thời lượng 45s (< 60s), khớp sub 100%. Đạt chuẩn!", "info");
    await sleep(1200);
    setNodeDone("review_video");

    setNodeRunning("generate_cover_image");
    await sleep(1200);
    setNodeDone("generate_cover_image");

    setNodeRunning("review_image");
    await sleep(1000);
    setNodeDone("review_image");

    updateActiveCount(0);
    logMessage("[HỘI TỤ] Cả 2 nhánh đã về đích! Dừng tại Touchpoint 3 (Duyệt trọn bộ)...", "system");

    const tp3El = document.getElementById("node-touchpoint-3");
    if (tp3El) {
        tp3El.style.borderColor = "#ffea00";
        tp3El.style.boxShadow = "0 0 35px rgba(255, 234, 0, 0.6)";
    }
    openTouchpoint3Modal();
}

function openTouchpoint3Modal() {
    document.getElementById("previewDraftText").innerText = 
`🚀 DỪNG VIẾT CONTENT BẰNG TAY NẾU BẠN KHÔNG MUỐN KIỆT SỨC VÀO NĂM 2026!

Bạn có nhận ra sự thật cay đắng này:
Mỗi tuần bạn tốn từ 20 đến 30 tiếng chỉ để vật lộn tìm ý tưởng, viết bài, dựng video rồi lại loay hoay căn chỉnh phụ đề?

Đó là lý do PoTa Content OS ra đời:
1. Agent 1-2 quét radar và lập kế hoạch tuần tự động.
2. Dây chuyền Chữ tự viết, rà soát chính tả và phân tách 3-5 bài Threads.
3. Dây chuyền Video tự động dựng 9:16 và sinh ảnh cover.

👉 Comment ngay "WORKFLOW" bên dưới để nhận tài liệu kiến trúc hệ thống 16 AI Agents hoàn toàn miễn phí!`;

    document.getElementById("previewThreadsList").innerHTML = `
        <div class="log-line">1/ Dừng viết content bằng tay nếu không muốn kiệt sức sau 2 tuần.</div>
        <div class="log-line">2/ Vấn đề lớn nhất: Cố làm tất cả một mình từ viết tới dựng video.</div>
        <div class="log-line">3/ Giải pháp mới: Chia nhỏ cho 16 AI Agent chuyên trách chạy song song.</div>
        <div class="log-line">4/ Kết quả: Tiết kiệm 80% thời gian mỗi tuần cho Solopreneurs.</div>
        <div class="log-line">5/ Bạn đã thử ứng dụng Agentic AI chưa? Thảo luận bên dưới nhé!</div>
    `;

    document.getElementById("previewCarouselSlides").innerHTML = `
        <div class="log-line">● Slide 1: Cách tự động hóa Content OS trong 3 bước</div>
        <div class="log-line">● Slide 2: Bước 1 - Quét radar đối thủ và lập lịch tuần</div>
        <div class="log-line">● Slide 3: Bước 2 - Dây chuyền Chữ tự sửa bài</div>
        <div class="log-line">● Slide 4: Bước 3 - Dây chuyền Video dựng 9:16</div>
        <div class="log-line">● Slide 5: Lưu lại bài viết nếu bạn thấy hữu ích!</div>
    `;

    document.getElementById("modalTouchpoint3").classList.add("active");
}

function switchPreviewTab(tabKey) {
    const tabs = document.querySelectorAll(".tab-btn");
    const panes = document.querySelectorAll(".tab-pane");

    tabs.forEach(t => t.classList.remove("active"));
    panes.forEach(p => p.classList.remove("active"));

    const activePane = document.getElementById(`pane-${tabKey}`);
    if (activePane) activePane.classList.add("active");
    event.target.classList.add("active");
}

async function submitTouchpoint3(isApproved) {
    closeModal("modalTouchpoint3");
    if (!isApproved) {
        logMessage("[Touchpoint 3] Yêu cầu chỉnh sửa lại. Đồ thị quay về nhánh sửa...", "warn");
        return;
    }

    logMessage("[Touchpoint 3] Phê duyệt trọn gói thành công! Kích hoạt Tầng Operations...", "success");

    updateActiveCount(2);
    setNodeRunning("publisher");
    logMessage("[Agent 14: Publisher] Đang xuất bản bài đăng đa kênh đồng bộ...", "info");
    await sleep(1500);
    setNodeDone("publisher");
    logMessage("  + Facebook: https://facebook.com/pota/posts/e82b14", "success");
    logMessage("  + TikTok:   https://tiktok.com/@pota/video/89f2a0", "success");
    logMessage("  + Threads:  https://threads.net/@pota/post/4c12d8", "success");
    logMessage("  + Shorts:   https://youtube.com/shorts/31ad0e", "success");

    setNodeRunning("comment_manager");
    logMessage("[Agent 15: Community] Kịch bản phản hồi CTA 'WORKFLOW' và seeding đã sẵn sàng!", "info");
    await sleep(1300);
    setNodeDone("comment_manager");

    setNodeRunning("analytics_learner");
    logMessage("[Agent 16: Analytics] Đo lường tuần: 145,000 views, 185 leads generated.", "info");
    await sleep(1500);
    setNodeDone("analytics_learner");

    updateActiveCount(0);
    setNodeDone("node-brain-update");
    setNodeDone("node-continuous-growth");

    logMessage("[HOÀN TẤT] Bộ nhận diện thương hiệu đã tự động cập nhật quy tắc mới!", "success");
    logMessage("🎉 PoTa Content OS đã hoàn thành xuất sắc 100% chu trình tuần!", "success");

    const btn = document.getElementById("btnStartFlow");
    btn.disabled = false;
    btn.innerHTML = "<span>⚡ RA LỆNH CHẠY</span>";
}

function handleResetWorkflow() {
    document.querySelectorAll(".agent-node").forEach(el => {
        el.classList.remove("node-running", "node-done", "waiting");
    });
    updateActiveCount(0);
    logMessage("[Reset] Đã đặt lại trạng thái các Agent về ban đầu.", "system");
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active");
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
