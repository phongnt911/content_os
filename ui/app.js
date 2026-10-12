/**
 * POTA Content OS - Visual Workflow Controller (app.js)
 * Điều khiển trạng thái thời gian thực của 16 Agents & 3 Human Touchpoints
 * Hỗ trợ đa ngành nghề (Industry-Agnostic) & Xử lý tương tác Human-in-the-loop hoàn chỉnh
 */

let workflowState = {
    isRunning: false,
    currentTouchpoint: null,
    activeAgentsCount: 0,
    currentTopic: "",
    planItems: [],
    selectedPlanIndex: 0,
    chosenArticle: null,
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

// ==========================================================================
// TERMINAL LOGS & UI HELPERS
// ==========================================================================
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

function resetAllNodes() {
    document.querySelectorAll(".agent-node").forEach(el => {
        el.classList.remove("node-running", "node-done", "waiting");
        el.style.borderColor = "";
        el.style.boxShadow = "";
    });
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove("active");
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ==========================================================================
// HỦY / DỪNG LUỒNG HOÀN TOÀN (FIX LỖI TỪ CHỐI NHƯNG VẪN THỂ HIỆN ĐANG CHẠY)
// ==========================================================================
function abortWorkflow(reason = "Người dùng đã từ chối kế hoạch") {
    closeModal("modalTouchpoint1");
    closeModal("modalTouchpoint2");
    closeModal("modalTouchpoint3");

    workflowState.isRunning = false;
    updateActiveCount(0);

    // Xóa toàn bộ trạng thái đang chạy hoặc đang chờ
    document.querySelectorAll(".agent-node").forEach(el => {
        el.classList.remove("node-running", "waiting");
    });

    const btn = document.getElementById("btnStartFlow");
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = "<span>⚡ RA LỆNH CHẠY</span>";
    }

    logMessage(`[ĐÃ DỪNG LUỒNG] ${reason}. Bạn có thể nhập chủ đề mới để bắt đầu lại bất cứ lúc nào.`, "warn");
}

function handleResetWorkflow() {
    resetAllNodes();
    abortWorkflow("Đã đặt lại toàn bộ hệ thống về ban đầu");
    clearLogs();
    logMessage("[POTA OS] Hệ thống đã sẵn sàng nhận lệnh mới.", "system");
}

// ==========================================================================
// KHỞI CHẠY QUY TRÌNH (START WORKFLOW)
// ==========================================================================
async function handleStartWorkflow() {
    const topicInput = document.getElementById("topicInput").value.trim();
    workflowState.currentTopic = topicInput;
    workflowState.isRunning = true;

    const btn = document.getElementById("btnStartFlow");
    btn.disabled = true;
    btn.innerHTML = "<span>⏳ ĐANG CHẠY...</span>";

    logMessage(`Khởi chạy POTA Content OS... Chủ đề: "${topicInput || 'Tự động quét radar đa ngành'}"`, "system");

    // Thử gọi Backend API server nếu đang mở server.py
    try {
        const res = await fetch("/api/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ focus_topic: topicInput })
        });
        if (res.ok) {
            const data = await res.json();
            logMessage("Đã kết nối trực tiếp StateGraph Backend!", "success");
            runConnectedBackendWorkflow(topicInput);
            return;
        }
    } catch (e) {
        // Fallback: Tự động chạy Smart Simulation Engine trực quan trên Client
    }

    logMessage("Kích hoạt Visual Engine trực quan trên giao diện...", "info");
    runSmartSimulation(topicInput);
}

// ==========================================================================
// THÍCH ỨNG ĐA NGÀNH (INDUSTRY-AGNOSTIC PLAN GENERATOR)
// ==========================================================================
function generateDynamicPlan(customTopic) {
    const raw = (customTopic || "").toLowerCase();
    const displayTopic = customTopic || "Chiến lược kinh doanh & Tăng trưởng số";

    if (raw.includes("ẩm thực") || raw.includes("f&b") || raw.includes("quán") || raw.includes("cà phê") || raw.includes("món ăn")) {
        return [
            { id: "post_01", channel: "Facebook", angle: `Góc tài chính F&B: 3 sai lầm khiến 80% quán lỗ trong 6 tháng đầu`, hook: "Đừng mở quán chỉ vì thích, nếu chưa nắm công thức cost 30% này!", core: "Quản trị dòng tiền và tỷ lệ giá vốn chuẩn xác cho quán" },
            { id: "post_02", channel: "TikTok", angle: `Case Study: Kéo 500 khách/ngày cho quán ăn nhờ video trải nghiệm hậu trường`, hook: "Quán vắng tanh thành kín bàn chỉ sau 1 tuần đổi cách quay clip", core: "Cách làm video chân thực thu hút thực khách địa phương" },
            { id: "post_03", channel: "Threads", angle: `Nghịch lý phục vụ: Khách hàng không nhớ món ngon, họ nhớ cảm xúc`, hook: "Tại sao khách sẵn sàng trả gấp đôi cho cùng 1 ly cà phê?", core: "Bí quyết tạo trải nghiệm khách hàng vượt trội" },
            { id: "post_04", channel: "Shorts", angle: `Quy trình kiểm soát nguyên liệu tươi ngon không tồn kho`, hook: "Cách chủ quán cắt giảm 20% lãng phí thực phẩm mỗi ngày", core: "Công thức nhập hàng theo định mức bán thực tế" }
        ];
    } else if (raw.includes("thời trang") || raw.includes("quần áo") || raw.includes("outfit") || raw.includes("mặc")) {
        return [
            { id: "post_01", channel: "Facebook", angle: `Bí quyết xây dựng tủ đồ Capsule Wardrobe 10 món phối 30 ngày`, hook: "Tủ đồ chật ních nhưng mỗi sáng bạn vẫn không có gì để mặc?", core: "Tối ưu chi phí trang phục và định hình phong cách cá nhân" },
            { id: "post_02", channel: "TikTok", angle: `3 lỗi phối đồ khiến người thấp bị dìm dáng mà 90% người mắc phải`, hook: "Chỉ cần đổi cách sơ vin này, nhìn bạn sẽ cao thêm 5cm ngay lập tức!", core: "Quy tắc tỷ lệ vàng 1/3 trong phối đồ thường ngày" },
            { id: "post_03", channel: "Threads", angle: `Tư duy mua sắm thông minh: Đừng mua theo trend, hãy tính Cost-Per-Wear`, hook: "Một chiếc áo 2 triệu có thể rẻ hơn chiếc áo 200k!", core: "Cách đầu tư thông minh vào chất lượng trang phục" },
            { id: "post_04", channel: "Shorts", angle: `Bảo quản trang phục cao cấp đúng cách tại nhà`, hook: "Sai lầm khi giặt giũ đang âm thầm phá hủy đồ đắt tiền của bạn", core: "Mẹo kéo dài tuổi thọ chất liệu vải lụa và len" }
        ];
    } else if (raw.includes("bất động sản") || raw.includes("nhà") || raw.includes("đất") || raw.includes("căn hộ")) {
        return [
            { id: "post_01", channel: "Facebook", angle: `Bẫy pháp lý khi mua nhà lần đầu và cách kiểm tra quy hoạch an toàn`, hook: "Đừng vội đặt cọc tiền tỷ nếu chưa xem 3 loại giấy tờ này!", core: "Quy trình thẩm định pháp lý và tránh tranh chấp quy hoạch" },
            { id: "post_02", channel: "TikTok", angle: `Bài toán đòn bẩy tài chính: Khi nào nên vay mua nhà?`, hook: "Vay 70% mua nhà: Đòn bẩy làm giàu hay chiếc thòng lọng nợ nần?", core: "Nguyên tắc an toàn không để tiền trả lãi vượt quá 40% thu nhập" },
            { id: "post_03", channel: "Threads", angle: `Kinh nghiệm chọn căn hộ chung cư không bao giờ mất giá`, hook: "Những chi tiết nhỏ khi đi xem nhà giúp bạn tránh mua phải căn lỗi", core: "Tiêu chí vị trí, ban quản lý và thiết kế phong thủy thông gió" },
            { id: "post_04", channel: "Shorts", angle: `Dự báo chu kỳ thị trường bất động sản thời gian tới`, hook: "Dòng tiền thông minh đang dịch chuyển về phân khúc nào?", core: "Nhận diện thời điểm gom hàng và giữ tiền mặt" }
        ];
    } else if (raw.includes("tài chính") || raw.includes("tiền") || raw.includes("đầu tư") || raw.includes("chi tiêu")) {
        return [
            { id: "post_01", channel: "Facebook", angle: `Phương pháp phân bổ tài chính 50/30/20 cho người trẻ dưới 30 tuổi`, hook: "Lương 20 triệu nhưng cuối tháng vẫn hết sạch tiền đi đâu?", core: "Kiểm soát chi tiêu vô thức và xây dựng quỹ dự phòng 6 tháng" },
            { id: "post_02", channel: "TikTok", angle: `Sai lầm đầu tư đu đỉnh: Tâm lý FOMO và cách trị dứt điểm`, hook: "Cứ mua là giảm, vừa bán thì tăng: Bạn có thấy quen không?", core: "Kỷ luật quản trị rủi ro và đầu tư định kỳ dài hạn" },
            { id: "post_03", channel: "Threads", angle: `Sức mạnh của lãi kép: Bắt đầu sớm quan trọng hơn bắt đầu nhiều`, hook: "1 triệu đồng mỗi tháng từ năm 20 tuổi sẽ biến thành bao nhiêu năm 40 tuổi?", core: "Tận dụng đòn bẩy thời gian trong tích lũy tài sản" },
            { id: "post_04", channel: "Shorts", angle: `Cách thoát khỏi bẫy nợ thẻ tín dụng lãi suất cao`, hook: "Ngân hàng kiếm tiền từ bạn như thế nào qua chiếc thẻ tín dụng?", core: "Chiến lược thanh toán dứt điểm dư nợ thông minh" }
        ];
    } else {
        // Đa ngành tổng quát / Chuyên sâu theo chủ đề nhập
        return [
            { id: "post_01", channel: "Facebook", angle: `Góc chuyên sâu: Giải mã bí quyết thực chiến về ${displayTopic}`, hook: `90% mọi người đang hiểu sai về "${displayTopic}" và cái giá phải trả...`, core: `Bản chất cốt lõi và phương pháp tiếp cận đúng đắn về ${displayTopic}` },
            { id: "post_02", channel: "TikTok", angle: `Case Study: Cách tạo đột phá với ${displayTopic} trong 30 ngày`, hook: `Tôi đã thay đổi hoàn toàn kết quả như thế nào nhờ áp dụng bí quyết này?`, core: `Quy trình thực tế từng bước (Step-by-Step) mang lại kết quả rõ rệt` },
            { id: "post_03", channel: "Threads", angle: `Nghịch lý: Làm ít hơn nhưng đạt hiệu quả cao hơn với ${displayTopic}`, hook: `Tại sao người giỏi nhất thường không phải người làm việc chăm chỉ nhất?`, core: `Tối ưu hóa đòn bẩy và tập trung vào 20% hành động tạo 80% kết quả` },
            { id: "post_04", channel: "Shorts", angle: `Sai lầm đắt giá cần tránh ngay lập tức khi triển khai ${displayTopic}`, hook: `Dừng lại ngay nếu bạn đang làm theo cách này!`, core: `Cảnh báo rủi ro thực tế và hướng dẫn giải pháp thay thế an toàn` }
        ];
    }
}

// ==========================================================================
// CLIENT SIMULATION ENGINE
// ==========================================================================
async function runSmartSimulation(customTopic) {
    updateActiveCount(2);
    setNodeRunning("research");
    logMessage(`[Agent 01: Research] Quét radar thảo luận & đối thủ xoay quanh: "${customTopic || 'Xu hướng đa ngành'}"...`, "info");
    await sleep(1400);
    setNodeDone("research");

    setNodeRunning("planner");
    logMessage("[Agent 02: Planner] Thiết lập ma trận kế hoạch tuần gồm 4-7 góc bài chuyên sâu...", "info");
    await sleep(1400);
    setNodeDone("planner");

    updateActiveCount(0);

    // Chuẩn bị ma trận bài viết cho Touchpoint 1
    workflowState.planItems = generateDynamicPlan(customTopic);
    workflowState.selectedPlanIndex = 0;

    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.add("waiting");
    logMessage("[TOUCHPOINT 1] Hệ thống tạm dừng chờ bạn phê duyệt Kế hoạch tuần!", "warn");

    openTouchpoint1Modal();
}

// ==========================================================================
// TOUCHPOINT 1 MODAL CONTROLLER
// ==========================================================================
function openTouchpoint1Modal() {
    togglePlanRejectView(false); // Đảm bảo mở ở chế độ xem bình thường
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
            <div class="card-hook" style="color: var(--text-muted); font-size: 11px; margin-top: 4px;">Thông điệp: ${item.core}</div>
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

// Chuyển đổi giữa Chế độ xem bài và Chế độ hỏi ngược lại nhu cầu đề tài
function togglePlanRejectView(showRefine) {
    const selView = document.getElementById("planSelectionView");
    const refView = document.getElementById("planRejectRefineView");
    const normFooter = document.getElementById("planNormalFooter");
    const refFooter = document.getElementById("planRefineFooter");

    if (showRefine) {
        selView.style.display = "none";
        refView.style.display = "block";
        normFooter.style.display = "none";
        refFooter.style.display = "flex";
        // Focus vào ô nhập nhu cầu
        setTimeout(() => {
            const input = document.getElementById("refinedTopicInput");
            if (input) input.focus();
        }, 100);
    } else {
        selView.style.display = "block";
        refView.style.display = "none";
        normFooter.style.display = "flex";
        refFooter.style.display = "none";
    }
}

// Người dùng nhập chủ đề mới và yêu cầu lập lại kế hoạch chuẩn xác hơn
async function submitReplanWithNewTopic() {
    const refinedTopic = document.getElementById("refinedTopicInput").value.trim();
    if (!refinedTopic) {
        alert("Vui lòng nhập chủ đề hoặc định hướng bạn muốn POTA tập trung!");
        return;
    }

    closeModal("modalTouchpoint1");
    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.remove("waiting");

    // Cập nhật lại thanh input trên cùng
    document.getElementById("topicInput").value = refinedTopic;
    workflowState.currentTopic = refinedTopic;

    logMessage(`[CHUYỂN HƯỚNG ĐỀ TÀI] Tiếp nhận yêu cầu: "${refinedTopic}". POTA quét radar và lập lại kế hoạch...`, "system");

    // Chạy lại Agent 1 và Agent 2
    runSmartSimulation(refinedTopic);
}

// Người dùng phê duyệt bài viết đã chọn
async function submitTouchpoint1(isApproved) {
    closeModal("modalTouchpoint1");
    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.remove("waiting");

    if (!isApproved) {
        // Đã được togglePlanRejectView xử lý, nếu gọi vào đây thì dừng an toàn
        abortWorkflow("Bạn đã từ chối kế hoạch");
        return;
    }

    const customVal = document.getElementById("customTopicInput").value.trim();
    const chosenPost = customVal ? {
        id: "post_custom",
        channel: "Facebook",
        angle: customVal,
        hook: `Sự thật đằng sau: ${customVal}`,
        core: customVal
    } : workflowState.planItems[workflowState.selectedPlanIndex];

    workflowState.chosenArticle = chosenPost;

    logMessage(`[Touchpoint 1] Phê duyệt thành công! Triển khai bài: "${chosenPost.angle}"`, "success");
    setNodeDone("node-touchpoint-1");

    // Rẽ nhánh song song 2 dây chuyền!
    updateActiveCount(2);
    runParallelPipelines(chosenPost);
}

// ==========================================================================
// DÂY CHUYỀN SONG SONG (FORK-JOIN PARALLEL PIPELINES)
// ==========================================================================
async function runParallelPipelines(chosenPost) {
    logMessage("[FORK] Đồ thị rẽ nhánh song song: Dây chuyền Chữ & Dây chuyền Video bắt đầu cùng lúc!", "system");

    // Nhánh Chữ: Dàn ý & Nhánh Video: Kịch bản
    setNodeRunning("generate_outline");
    setNodeRunning("generate_video_script");
    logMessage(`[Agent 03: Outline] Thiết kế dàn ý 3 hook & luận điểm cho "${chosenPost.channel}"...`, "info");
    logMessage(`[Agent 09: Script] Soạn thảo kịch bản video dọc 9:16 (30-50s)...`, "info");
    await sleep(1500);
    setNodeDone("generate_outline");
    setNodeDone("generate_video_script");

    // Nhánh Video tạm dừng chờ Creator quay raw footage tại Touchpoint 2
    const tp2El = document.getElementById("node-touchpoint-2");
    if (tp2El) tp2El.classList.add("waiting");
    logMessage("[TOUCHPOINT 2] Kịch bản video đã xong! Chờ Creator quay video footage...", "warn");

    // Trong khi đó nhánh Chữ vẫn tiếp tục chạy độc lập:
    setNodeRunning("writer");
    logMessage("[Agent 04: Writer] Chấp bút bài viết hoàn chỉnh chuẩn phong cách POTA...", "info");
    await sleep(1500);
    setNodeDone("writer");

    setNodeRunning("review_text");
    logMessage("[Agent 05: QA Review] Chấm điểm chất lượng: 9.2/10 (Đạt chuẩn xuất sắc). Cho phép đi tiếp!", "info");
    await sleep(1200);
    setNodeDone("review_text");

    setNodeRunning("fact_check");
    logMessage("[Agent 06: Fact-check] Quét lỗi chính tả và rà soát chính sách phân phối Meta/TikTok...", "info");
    await sleep(1000);
    setNodeDone("fact_check");

    setNodeRunning("repurpose_threads");
    logMessage("[Agent 07: Repurpose] Chuyển thể thành chuỗi 4 post Threads viral...", "info");
    await sleep(1200);
    setNodeDone("repurpose_threads");

    setNodeRunning("generate_carousel");
    logMessage("[Agent 08: Carousel] Thiết kế bộ slide Carousel 5 trang cho Instagram/Facebook...", "info");
    await sleep(1200);
    setNodeDone("generate_carousel");
    logMessage("[Dây chuyền Chữ] ĐÃ HOÀN TẤT VÀ VỀ ĐÍCH! Sẵn sàng hội tụ...", "success");

    // Bật modal Touchpoint 2 để creator nạp clip
    openTouchpoint2Modal(chosenPost);
}

// ==========================================================================
// TOUCHPOINT 2 MODAL (CREATOR QUAY RAW FOOTAGE)
// ==========================================================================
function openTouchpoint2Modal(post) {
    const hookEl = document.getElementById("scriptHook");
    if (hookEl) hookEl.innerText = `"${post.hook}"`;

    const scenesEl = document.getElementById("scriptScenesList");
    if (scenesEl) {
        scenesEl.innerHTML = `
            <div class="script-scene-item">
                <div class="scene-num">Cảnh 1 (0-3s)</div>
                <div class="scene-desc"><strong>Visual:</strong> Creator nhìn thẳng ống kính, biểu cảm ngạc nhiên / chỉ tay nhấn mạnh.</div>
                <div class="scene-voice"><strong>Voice:</strong> "${post.hook}"</div>
            </div>
            <div class="script-scene-item">
                <div class="scene-num">Cảnh 2 (4-25s)</div>
                <div class="scene-desc"><strong>Visual:</strong> Chèn B-roll minh họa / bảng biểu dẫn chứng cụ thể.</div>
                <div class="scene-voice"><strong>Voice:</strong> "Vấn đề là 90% mọi người đang tiếp cận sai cách. Bản chất ở đây là ${post.core}..."</div>
            </div>
            <div class="script-scene-item">
                <div class="scene-num">Cảnh 3 (26-45s)</div>
                <div class="scene-desc"><strong>Visual:</strong> Creator mỉm cười, chỉ tay xuống phần bình luận. Xuất hiện logo POTA.</div>
                <div class="scene-voice"><strong>Voice:</strong> "Comment từ khóa 'CHI TIẾT' bên dưới để nhận tài liệu hướng dẫn đầy đủ nhé!"</div>
            </div>
        `;
    }

    document.getElementById("modalTouchpoint2").classList.add("active");
}

async function submitTouchpoint2() {
    closeModal("modalTouchpoint2");
    const tp2El = document.getElementById("node-touchpoint-2");
    if (tp2El) tp2El.classList.remove("waiting");
    setNodeDone("node-touchpoint-2");

    const url = document.getElementById("rawFootageInput").value.trim() || "https://drive.google.com/sample_footage.mp4";
    logMessage(`[Touchpoint 2] Đã nạp footage video thô: ${url}`, "success");

    // Tiếp tục nhánh Video: Dựng & Review
    updateActiveCount(2);
    setNodeRunning("video_editing");
    logMessage("[Agent 10: Video Editor] Tự động cắt khoảng lặng, tạo phụ đề động và ghép nhạc nền...", "info");
    await sleep(1600);
    setNodeDone("video_editing");

    setNodeRunning("review_video");
    logMessage("[Agent 11: Review Video] Thời lượng 42s (< 60s), khớp phụ đề 100%. Đạt chuẩn phát hành!", "info");
    await sleep(1200);
    setNodeDone("review_video");

    setNodeRunning("generate_cover_image");
    logMessage("[Agent 12: Cover Artist] Tạo prompt sinh ảnh thumbnail tỉ lệ 3:4 và 9:16...", "info");
    await sleep(1200);
    setNodeDone("generate_cover_image");

    setNodeRunning("review_image");
    logMessage("[Agent 13: Review Cover] Tiêu đề nằm trong safe zone, độ tương phản cao. Đạt chuẩn!", "info");
    await sleep(1000);
    setNodeDone("review_image");

    updateActiveCount(0);
    logMessage("[HỘI TỤ ĐỒ THỊ] Hai dây chuyền Chữ và Video đã hoàn thành! Dừng tại Touchpoint 3...", "system");

    const tp3El = document.getElementById("node-touchpoint-3");
    if (tp3El) {
        tp3El.style.borderColor = "#ffea00";
        tp3El.style.boxShadow = "0 0 35px rgba(255, 234, 0, 0.6)";
    }
    openTouchpoint3Modal();
}

// ==========================================================================
// TOUCHPOINT 3 MODAL (DUYỆT TRỌN BỘ ẤN PHẨM TRƯỚC XUẤT BẢN)
// ==========================================================================
function openTouchpoint3Modal() {
    const post = workflowState.chosenArticle || {
        angle: "Chiến lược nội dung thực chiến",
        hook: "Đừng làm theo cách cũ nếu không muốn tụt lại phía sau",
        core: "Tập trung vào giá trị cốt lõi"
    };

    document.getElementById("previewDraftText").innerText = 
`🚀 ${post.hook.toUpperCase()}!

Bạn có nhận ra sự thật cay đắng này:
Đa phần mọi người tốn hàng chục tiếng mỗi tuần nhưng kết quả vẫn giậm chân tại chỗ vì thiếu một quy trình thực thi chuẩn mực.

Đó là lý do POTA Content OS đồng hành cùng bạn:
1. Xác định đúng điểm nghẽn và nỗi đau thực tế của độc giả.
2. Cung cấp giải pháp rõ ràng, đo lường được và áp dụng được ngay: ${post.core}.
3. Tối ưu hóa chuỗi phân phối đa kênh để tối đa hóa độ phủ sóng.

👉 Comment ngay từ khóa "CHI TIẾT" bên dưới để nhận tài liệu phân tích chuyên sâu hoàn toàn miễn phí!`;

    document.getElementById("previewThreadsList").innerHTML = `
        <div class="log-line">1/ ${post.hook}.</div>
        <div class="log-line">2/ Sai lầm phổ biến nhất: Cố làm tất cả một mình mà không có hệ thống hỗ trợ.</div>
        <div class="log-line">3/ Giải pháp: Áp dụng nguyên lý cốt lõi: ${post.core}.</div>
        <div class="log-line">4/ Kết quả: Tiết kiệm 80% thời gian mà chất lượng nội dung vượt trội.</div>
        <div class="log-line">5/ Bạn nghĩ sao về góc nhìn này? Thảo luận bên dưới nhé!</div>
    `;

    document.getElementById("previewCarouselSlides").innerHTML = `
        <div class="log-line">● Slide 1: ${post.hook}</div>
        <div class="log-line">● Slide 2: Vấn đề 90% người gặp phải</div>
        <div class="log-line">● Slide 3: Giải pháp cốt lõi: ${post.core}</div>
        <div class="log-line">● Slide 4: 3 bước hành động ngay hôm nay</div>
        <div class="log-line">● Slide 5: Lưu lại bài viết nếu bạn thấy hữu ích!</div>
    `;

    document.getElementById("previewCoverHeadline").innerText = post.hook.slice(0, 35).toUpperCase();
    document.getElementById("modalTouchpoint3").classList.add("active");
}

function switchPreviewTab(tabKey) {
    const tabs = document.querySelectorAll(".tab-btn");
    const panes = document.querySelectorAll(".tab-pane");

    tabs.forEach(t => t.classList.remove("active"));
    panes.forEach(p => p.classList.remove("active"));

    const activePane = document.getElementById(`pane-${tabKey}`);
    if (activePane) activePane.classList.add("active");
    if (event && event.target) event.target.classList.add("active");
}

async function submitTouchpoint3(isApproved) {
    closeModal("modalTouchpoint3");
    if (!isApproved) {
        const note = document.getElementById("revisionNoteInput").value.trim() || "Chỉnh sửa hoàn thiện";
        logMessage(`[Touchpoint 3] Yêu cầu chỉnh sửa: "${note}". Chuyển lại cho Writer & Video Editor...`, "warn");
        
        // Giả lập sửa nhanh
        setNodeRunning("writer");
        await sleep(1000);
        setNodeDone("writer");
        logMessage("[Touchpoint 3] Đã tinh chỉnh bài viết theo yêu cầu! Mời bạn duyệt lại.", "info");
        openTouchpoint3Modal();
        return;
    }

    logMessage("[Touchpoint 3] Phê duyệt trọn gói thành công! Kích hoạt Tầng Operations...", "success");

    updateActiveCount(2);
    setNodeRunning("publisher");
    logMessage("[Agent 14: Publisher] Xuất bản bài đăng đồng bộ đa nền tảng...", "info");
    await sleep(1500);
    setNodeDone("publisher");
    logMessage("  + Facebook: https://facebook.com/pota/posts/e82b14", "success");
    logMessage("  + TikTok:   https://tiktok.com/@pota/video/89f2a0", "success");
    logMessage("  + Threads:  https://threads.net/@pota/post/4c12d8", "success");
    logMessage("  + Shorts:   https://youtube.com/shorts/31ad0e", "success");

    setNodeRunning("comment_manager");
    logMessage("[Agent 15: Community] Kịch bản phản hồi tự động CTA và seeding chuyên môn đã kích hoạt!", "info");
    await sleep(1300);
    setNodeDone("comment_manager");

    setNodeRunning("analytics_learner");
    logMessage("[Agent 16: Analytics] Tổng kết số liệu: 145,000 lượt xem, 185 lượt chuyển đổi thành công.", "info");
    await sleep(1500);
    setNodeDone("analytics_learner");

    updateActiveCount(0);
    setNodeDone("node-brain-update");
    setNodeDone("node-continuous-growth");

    logMessage("[HOÀN TẤT] Brand Brain đã tự động cập nhật bài học chiến thắng vào Bộ quy chuẩn!", "success");
    logMessage("🎉 POTA Content OS đã hoàn thành xuất sắc 100% chu trình tuần!", "success");

    // Khôi phục nút chạy
    workflowState.isRunning = false;
    const btn = document.getElementById("btnStartFlow");
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = "<span>⚡ RA LỆNH CHẠY</span>";
    }
}
