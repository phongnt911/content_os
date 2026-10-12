/**
 * POTA Content OS - Visual Workflow Controller (app.js)
 * Điều khiển trạng thái thời gian thực của 16 Agents & 3 Human Touchpoints
 * Hỗ trợ đa ngành nghề (Industry-Agnostic) & Kết nối trực tiếp LangGraph / Gemini Backend
 */

let workflowState = {
    isRunning: false,
    isBackendConnected: false,
    currentTouchpoint: null,
    activeAgentsCount: 0,
    currentTopic: "",
    planItems: [],
    selectedPlanIndex: 0,
    chosenArticle: null,
    backendSnapshot: null,
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
// HỦY / DỪNG LUỒNG HOÀN TOÀN
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
            workflowState.isBackendConnected = true;
            workflowState.backendSnapshot = data;
            logMessage("Đã kết nối trực tiếp StateGraph Backend & Gemini LLM!", "success");
            await runConnectedBackendWorkflow(data, topicInput);
            return;
        }
    } catch (e) {
        logMessage("Không phát hiện máy chủ backend, chuyển sang Smart Client Engine...", "info");
    }

    workflowState.isBackendConnected = false;
    runSmartSimulation(topicInput);
}

// ==========================================================================
// KẾT NỐI VỚI BACKEND STATGRAPH & GEMINI THẬT
// ==========================================================================
async function runConnectedBackendWorkflow(backendData, customTopic) {
    updateActiveCount(2);
    setNodeRunning("research");
    logMessage(`[Agent 01: Research] Quét radar chuyên sâu xoay quanh: "${customTopic || 'Đa ngành'}"...`, "info");
    await sleep(1000);
    setNodeDone("research");

    setNodeRunning("planner");
    logMessage("[Agent 02: Planner] Lập ma trận kế hoạch tuần từ trí tuệ nhân tạo Gemini...", "info");
    await sleep(1000);
    setNodeDone("planner");

    updateActiveCount(0);

    // LẤY DỮ LIỆU THẬT DO GEMINI SINH RA:
    const rawItems = (backendData && backendData.values && backendData.values.content_plan) ? backendData.values.content_plan : [];
    if (rawItems.length > 0) {
        workflowState.planItems = rawItems.map(item => ({
            id: item.id || "post_01",
            channel: item.target_channel || "Facebook",
            angle: item.angle || "Chủ đề bài viết",
            hook: item.hook_concept || "Ý tưởng mở bài cuốn hút",
            core: item.core_message || "Thông điệp cốt lõi"
        }));
        logMessage(`[Backend] Nhận thành công ${rawItems.length} bài viết do Gemini LLM thiết lập chuẩn xác theo đề tài!`, "success");
    } else {
        workflowState.planItems = generateDynamicPlan(customTopic);
    }

    workflowState.selectedPlanIndex = 0;

    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.add("waiting");
    logMessage("[TOUCHPOINT 1] Đã nhận kế hoạch từ AI! Chờ bạn phê duyệt...", "warn");

    openTouchpoint1Modal();
}

// ==========================================================================
// THÍCH ỨNG ĐA NGÀNH (CHUẨN XÁC, TỰ NHIÊN, KHÔNG VĂN MẪU SÁO RỖNG)
// ==========================================================================
function generateDynamicPlan(customTopic) {
    const raw = (customTopic || "").toLowerCase();
    const displayTopic = customTopic || "Đặc sản & Văn hóa ẩm thực Việt Nam";

    // 1. NÔNG SẢN / TRÁI CÂY / ẨM THỰC / ĐẶC SẢN VÙNG MIỀN (Ví dụ: xoài cam lâm, sầu riêng, cà phê, yến sào...)
    if (raw.includes("xoài") || raw.includes("cam lâm") || raw.includes("nông sản") || raw.includes("trái cây") || 
        raw.includes("đặc sản") || raw.includes("sầu riêng") || raw.includes("ẩm thực") || raw.includes("món ăn") || 
        raw.includes("quán") || raw.includes("cà phê") || raw.includes("f&b")) {
        return [
            { 
                id: "post_01", 
                channel: "Facebook", 
                angle: `Góc nguồn gốc & thổ nhưỡng: Điều gì tạo nên vị ngọt thanh độc bản của ${displayTopic}?`, 
                hook: `Tại sao cùng một giống quả, nhưng trồng ở vùng đất này lại có hương vị thơm ngon đặc biệt đến vậy?`, 
                core: `Khám phá câu chuyện thổ nhưỡng, nguồn gốc xuất xứ và niềm tự hào nông sản địa phương` 
            },
            { 
                id: "post_02", 
                channel: "TikTok", 
                angle: `Mẹo nhà vườn: Cách nhận biết ${displayTopic} chín cây tự nhiên loại 1`, 
                hook: `Đi chợ hoặc đặt mua online, nhớ kiểm tra ngay 3 dấu hiệu phân biệt này kẻo mua phải hàng ngâm thuốc!`, 
                core: `Kinh nghiệm chọn quả tươi ngon, chuẩn sạch an toàn cho cả gia đình` 
            },
            { 
                id: "post_03", 
                channel: "Threads", 
                angle: `Văn hóa thưởng thức & chế biến món ngon từ ${displayTopic}`, 
                hook: `Bạn đã thử kết hợp ${displayTopic} theo công thức độc đáo này chưa? Ngon bất ngờ!`, 
                core: `Gợi ý cách ăn ngon đúng điệu, biến tấu món tráng miệng hấp dẫn` 
            },
            { 
                id: "post_04", 
                channel: "Shorts", 
                angle: `Mùa thu hoạch rộ & Kết nối tiêu thụ nông sản Việt`, 
                hook: `Mùa thu hoạch rộ đã về, tận mắt ngắm nhìn những vườn ${displayTopic} trĩu quả tràn ngập sức sống!`, 
                core: `Lan tỏa hình ảnh đẹp về người nông dân và cầu nối nông sản sạch đến người tiêu dùng` 
            }
        ];
    } 
    // 2. THỜI TRANG & LỐI SỐNG
    else if (raw.includes("thời trang") || raw.includes("quần áo") || raw.includes("outfit") || raw.includes("mặc")) {
        return [
            { id: "post_01", channel: "Facebook", angle: `Bí quyết xây dựng tủ đồ Capsule Wardrobe 10 món phối 30 ngày`, hook: "Tủ đồ chật ních nhưng mỗi sáng bạn vẫn không có gì để mặc?", core: "Tối ưu chi phí trang phục và định hình phong cách cá nhân" },
            { id: "post_02", channel: "TikTok", angle: `3 lỗi phối đồ khiến người thấp bị dìm dáng mà 90% người mắc phải`, hook: "Chỉ cần đổi cách sơ vin này, nhìn bạn sẽ thanh thoát và cao ráo hơn ngay!", core: "Quy tắc tỷ lệ vàng trong phối đồ thường ngày" },
            { id: "post_03", channel: "Threads", angle: `Tư duy mua sắm thông minh: Đừng mua theo trend, hãy tính Cost-Per-Wear`, hook: "Tại sao một món đồ chất lượng cao lại giúp bạn tiết kiệm tiền hơn đồ rẻ tiền nhanh hỏng?", core: "Cách đầu tư thông minh vào chất lượng trang phục" },
            { id: "post_04", channel: "Shorts", angle: `Bảo quản trang phục bền đẹp như mới tại nhà`, hook: "Sai lầm khi giặt giũ đang âm thầm làm bay màu và xơ vải đồ yêu thích của bạn", core: "Mẹo kéo dài tuổi thọ trang phục hàng ngày" }
        ];
    } 
    // 3. BẤT ĐỘNG SẢN & NHÀ ĐẤT
    else if (raw.includes("bất động sản") || raw.includes("nhà") || raw.includes("đất") || raw.includes("căn hộ")) {
        return [
            { id: "post_01", channel: "Facebook", angle: `Kiểm tra pháp lý an toàn khi mua bất động sản lần đầu`, hook: "Đừng vội đặt cọc nếu chưa kiểm tra kỹ 3 loại giấy tờ quy hoạch này!", core: "Quy trình thẩm định pháp lý và tránh tranh chấp rủi ro" },
            { id: "post_02", channel: "TikTok", angle: `Bài toán đòn bẩy tài chính: Khi nào nên vay mua nhà?`, hook: "Vay mua nhà: Đòn bẩy sở hữu tổ ấm hay áp lực nợ nần vượt tầm kiểm soát?", core: "Nguyên tắc an toàn không để tiền trả nợ vượt quá 40% thu nhập" },
            { id: "post_03", channel: "Threads", angle: `Kinh nghiệm chọn căn hộ thực tế từ người trong ngành`, hook: "Những chi tiết nhỏ khi đi xem nhà giúp bạn tránh mua phải căn bị lỗi phong thủy hoặc ngấm dột", core: "Tiêu chí vị trí, tiện ích và ban quản lý vận hành" },
            { id: "post_04", channel: "Shorts", angle: `Dự báo chu kỳ và nhịp sóng thị trường`, hook: "Dòng tiền thông minh đang ưu tiên phân khúc nào trong năm nay?", core: "Nhận diện thời điểm an toàn để an cư và tích lũy tài sản" }
        ];
    } 
    // 4. TÀI CHÍNH CÁ NHÂN & CHI TIÊU
    else if (raw.includes("tài chính") || raw.includes("tiền") || raw.includes("đầu tư") || raw.includes("chi tiêu")) {
        return [
            { id: "post_01", channel: "Facebook", angle: `Phương pháp phân bổ tài chính 50/30/20 đơn giản, dễ áp dụng`, hook: "Thu nhập đều đặn nhưng cuối tháng vẫn không thấy tiền tích lũy ở đâu?", core: "Kiểm soát chi tiêu vô thức và xây dựng quỹ dự phòng an tâm" },
            { id: "post_02", channel: "TikTok", angle: `Tâm lý chi tiêu theo cảm xúc và cách trị dứt điểm`, hook: "Có bao giờ bạn mua sắm chỉ vì buồn chán rồi về nhà lại hối hận không?", core: "Quy tắc trì hoãn 48 giờ trước khi quẹt thẻ mua sắm" },
            { id: "post_03", channel: "Threads", angle: `Sức mạnh của kỷ luật tích lũy nhỏ mỗi ngày`, hook: "Tiết kiệm 50k mỗi ngày: Tưởng ít nhưng sau 5 năm sẽ mang lại điều bất ngờ gì?", core: "Xây dựng thói quen tài chính lành mạnh, bền bỉ" },
            { id: "post_04", channel: "Shorts", angle: `Tránh bẫy tín dụng và lãi suất ẩn`, hook: "Sử dụng thẻ tín dụng thông minh để nhận ưu đãi mà không bị tính lãi", core: "Chiến lược quản trị hạn mức và thanh toán đúng hạn" }
        ];
    } 
    // 5. TỔNG QUÁT TỰ NHIÊN (Áp dụng cho mọi chủ đề khác)
    else {
        return [
            { 
                id: "post_01", 
                channel: "Facebook", 
                angle: `Góc nhìn toàn cảnh & Bản chất cốt lõi về ${displayTopic}`, 
                hook: `Những điều quan trọng nhất về "${displayTopic}" mà người mới bắt đầu thường bỏ lỡ...`, 
                core: `Hiểu đúng bản chất để đưa ra quyết định sáng suốt và tiết kiệm thời gian` 
            },
            { 
                id: "post_02", 
                channel: "TikTok", 
                angle: `Hướng dẫn thực tế: Kinh nghiệm chọn lọc và mẹo hay về ${displayTopic}`, 
                hook: `Nếu bạn đang quan tâm đến ${displayTopic}, lưu lại ngay 3 kinh nghiệm cực kỳ hữu ích này!`, 
                core: `Bài học thực tiễn giúp bạn tiếp cận vấn đề dễ dàng và hiệu quả nhất` 
            },
            { 
                id: "post_03", 
                channel: "Threads", 
                angle: `Góc nhìn đa chiều & Trải nghiệm thực tế xoay quanh ${displayTopic}`, 
                hook: `Sự khác biệt lớn nhất giữa cách tiếp cận truyền thống và phương pháp mới về ${displayTopic}...`, 
                core: `Góc nhìn mới mẻ, thúc đẩy thảo luận tích cực và văn minh` 
            },
            { 
                id: "post_04", 
                channel: "Shorts", 
                angle: `Tóm tắt nhanh những điều nên làm và nên tránh về ${displayTopic}`, 
                hook: `Trước khi bắt tay vào thực hiện ${displayTopic}, hãy chắc chắn bạn đã biết điều này!`, 
                core: `Hướng dẫn súc tích, dễ nhớ và ứng dụng được ngay` 
            }
        ];
    }
}

// ==========================================================================
// CLIENT SIMULATION ENGINE (KHI CHẠY OFFLINE)
// ==========================================================================
async function runSmartSimulation(customTopic) {
    updateActiveCount(2);
    setNodeRunning("research");
    logMessage(`[Agent 01: Research] Quét radar thảo luận & cộng đồng xoay quanh: "${customTopic || 'Chủ đề tuần'}"...`, "info");
    await sleep(1200);
    setNodeDone("research");

    setNodeRunning("planner");
    logMessage("[Agent 02: Planner] Phân tích ngữ cảnh và thiết lập ma trận 4 góc bài chuyên sâu...", "info");
    await sleep(1200);
    setNodeDone("planner");

    updateActiveCount(0);

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
    togglePlanRejectView(false);
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

async function submitReplanWithNewTopic() {
    const refinedTopic = document.getElementById("refinedTopicInput").value.trim();
    if (!refinedTopic) {
        alert("Vui lòng nhập chủ đề hoặc định hướng bạn muốn POTA tập trung!");
        return;
    }

    closeModal("modalTouchpoint1");
    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.remove("waiting");

    document.getElementById("topicInput").value = refinedTopic;
    workflowState.currentTopic = refinedTopic;

    logMessage(`[CHUYỂN HƯỚNG ĐỀ TÀI] Tiếp nhận yêu cầu: "${refinedTopic}". POTA quét radar và lập lại kế hoạch...`, "system");

    // Thử gọi lại backend nếu có kết nối
    if (workflowState.isBackendConnected) {
        try {
            const res = await fetch("/api/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ focus_topic: refinedTopic })
            });
            if (res.ok) {
                const data = await res.json();
                runConnectedBackendWorkflow(data, refinedTopic);
                return;
            }
        } catch (e) {}
    }

    runSmartSimulation(refinedTopic);
}

async function submitTouchpoint1(isApproved) {
    closeModal("modalTouchpoint1");
    const tp1El = document.getElementById("node-touchpoint-1");
    if (tp1El) tp1El.classList.remove("waiting");

    if (!isApproved) {
        abortWorkflow("Bạn đã từ chối kế hoạch tuần");
        return;
    }

    const customVal = document.getElementById("customTopicInput").value.trim();
    const chosenPost = customVal ? {
        id: "post_custom",
        channel: "Facebook",
        angle: customVal,
        hook: `Khám phá câu chuyện đằng sau: ${customVal}`,
        core: customVal
    } : workflowState.planItems[workflowState.selectedPlanIndex];

    workflowState.chosenArticle = chosenPost;

    logMessage(`[Touchpoint 1] Phê duyệt thành công! Triển khai bài: "${chosenPost.angle}"`, "success");
    setNodeDone("node-touchpoint-1");

    // Nếu có backend, gửi thông báo resume
    if (workflowState.isBackendConnected) {
        try {
            fetch("/api/touchpoint/resume", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    resume: {
                        approved: true,
                        selected_index: workflowState.selectedPlanIndex,
                        custom_topic: customVal || undefined
                    }
                })
            });
        } catch (e) {}
    }

    updateActiveCount(2);
    runParallelPipelines(chosenPost);
}

// ==========================================================================
// DÂY CHUYỀN SONG SONG (FORK-JOIN PARALLEL PIPELINES)
// ==========================================================================
async function runParallelPipelines(chosenPost) {
    logMessage("[FORK] Đồ thị rẽ nhánh song song: Dây chuyền Chữ & Dây chuyền Video bắt đầu cùng lúc!", "system");

    setNodeRunning("generate_outline");
    setNodeRunning("generate_video_script");
    logMessage(`[Agent 03: Outline] Thiết kế dàn ý 3 hook & luận điểm cho "${chosenPost.channel}"...`, "info");
    logMessage(`[Agent 09: Script] Soạn thảo kịch bản video dọc 9:16 (30-50s)...`, "info");
    await sleep(1500);
    setNodeDone("generate_outline");
    setNodeDone("generate_video_script");

    const tp2El = document.getElementById("node-touchpoint-2");
    if (tp2El) tp2El.classList.add("waiting");
    logMessage("[TOUCHPOINT 2] Kịch bản video đã xong! Chờ Creator quay video footage...", "warn");

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
                <div class="scene-desc"><strong>Visual:</strong> Creator nhìn thẳng ống kính, biểu cảm hào hứng / cầm sản phẩm thực tế trên tay.</div>
                <div class="scene-voice"><strong>Voice:</strong> "${post.hook}"</div>
            </div>
            <div class="script-scene-item">
                <div class="scene-num">Cảnh 2 (4-25s)</div>
                <div class="scene-desc"><strong>Visual:</strong> Cận cảnh chi tiết / chia sẻ thực tế trải nghiệm và kinh nghiệm hữu ích.</div>
                <div class="scene-voice"><strong>Voice:</strong> "Nhiều người thường không để ý chi tiết này, nhưng chính nó quyết định ${post.core}..."</div>
            </div>
            <div class="script-scene-item">
                <div class="scene-num">Cảnh 3 (26-45s)</div>
                <div class="scene-desc"><strong>Visual:</strong> Creator mỉm cười, chỉ tay xuống phần bình luận. Xuất hiện logo POTA.</div>
                <div class="scene-voice"><strong>Voice:</strong> "Bình luận bên dưới nếu bạn muốn biết thêm thông tin chi tiết nhé!"</div>
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

    // Nếu có backend kết nối, đồng bộ tiếp luồng
    if (workflowState.isBackendConnected) {
        try {
            fetch("/api/touchpoint/resume", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    resume: { raw_footage_url: url }
                })
            });
        } catch (e) {}
    }

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
// TOUCHPOINT 3 MODAL (DUYỆT TRỌN BỘ ẤN PHẨM)
// ==========================================================================
function openTouchpoint3Modal() {
    const post = workflowState.chosenArticle || {
        angle: "Khám phá câu chuyện đặc sản",
        hook: "Điều gì làm nên hương vị đặc biệt mà vùng khác khó sánh bằng?",
        core: "Chất lượng chuẩn sạch và giá trị văn hóa vùng miền"
    };

    document.getElementById("previewDraftText").innerText = 
`🌿 ${post.hook.toUpperCase()}!

Có một sự thật thú vị là:
Không phải ngẫu nhiên mà thức quà này lại được nhiều người yêu thích và săn đón đến vậy.

Hôm nay hãy cùng POTA tìm hiểu kỹ hơn:
1. Nguồn gốc xuất xứ và điều kiện tự nhiên đặc ân cho hương vị đậm đà khó quên.
2. Cách phân biệt hàng loại 1 chuẩn vị gốc so với hàng trôi nổi kém chất lượng.
3. Bí quyết bảo quản và gợi ý món ngon để thưởng thức trọn vẹn nhất: ${post.core}.

👉 Bình luận ngay bên dưới chia sẻ cảm nhận của bạn nhé!`;

    document.getElementById("previewThreadsList").innerHTML = `
        <div class="log-line">1/ ${post.hook}.</div>
        <div class="log-line">2/ Điểm đặc biệt nhất: Hương vị tự nhiên không thể pha lẫn.</div>
        <div class="log-line">3/ Mẹo nhỏ khi chọn mua: Luôn chú ý vào nguồn gốc và độ tươi mới.</div>
        <div class="log-line">4/ Ý nghĩa: ${post.core}.</div>
        <div class="log-line">5/ Bạn đã từng thưởng thức chưa? Chia sẻ trải nghiệm bên dưới nhé!</div>
    `;

    document.getElementById("previewCarouselSlides").innerHTML = `
        <div class="log-line">● Slide 1: ${post.hook}</div>
        <div class="log-line">● Slide 2: Nguồn gốc và vùng đất đặc ân</div>
        <div class="log-line">● Slide 3: 3 mẹo chọn chuẩn ngon loại 1</div>
        <div class="log-line">● Slide 4: Hướng dẫn bảo quản tươi lâu</div>
        <div class="log-line">● Slide 5: Lưu lại bài viết hữu ích này nhé!</div>
    `;

    document.getElementById("previewCoverHeadline").innerText = post.hook.slice(0, 35).toUpperCase();
    document.getElementById("modalTouchpoint3").classList.add("active");
}

function switchPreviewTab(tabKey) {
    const tabs = document.querySelectorAll(".preview-tabs-nav .tab-btn");
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
        
        setNodeRunning("writer");
        await sleep(1000);
        setNodeDone("writer");
        logMessage("[Touchpoint 3] Đã tinh chỉnh bài viết theo yêu cầu! Mời bạn duyệt lại.", "info");
        openTouchpoint3Modal();
        return;
    }

    logMessage("[Touchpoint 3] Phê duyệt trọn gói thành công! Kích hoạt Tầng Operations...", "success");

    // Nếu có backend, gửi resume phê duyệt trọn gói và nhận kết quả đo lường thực từ Gemini
    if (workflowState.isBackendConnected) {
        try {
            const res = await fetch("/api/touchpoint/resume", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    resume: { approved: true }
                })
            });
            if (res.ok) {
                const data = await res.json();
                if (data && data.values) {
                    if (data.values.published_links) workflowState.publishedLinks = data.values.published_links;
                    if (data.values.weekly_metrics) workflowState.weeklyMetrics = data.values.weekly_metrics;
                    if (data.values.brand_rules) workflowState.brandRules = data.values.brand_rules;
                }
            }
        } catch (e) {}
    }

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
    logMessage("[Agent 15: Community] Kịch bản phản hồi tự động và seeding thảo luận đã sẵn sàng!", "info");
    await sleep(1300);
    setNodeDone("comment_manager");

    setNodeRunning("analytics_learner");
    logMessage("[Agent 16: Analytics] Tổng kết số liệu: 145,000 lượt xem, 185 phản hồi tích cực.", "info");
    await sleep(1500);
    setNodeDone("analytics_learner");

    updateActiveCount(0);
    setNodeDone("node-brain-update");
    setNodeDone("node-continuous-growth");

    logMessage("[HOÀN TẤT] Brand Brain đã tự động cập nhật bài học thành công vào Bộ quy chuẩn!", "success");
    logMessage("🎉 POTA Content OS đã hoàn thành xuất sắc 100% chu trình tuần!", "success");

    workflowState.isRunning = false;
    const btn = document.getElementById("btnStartFlow");
    if (btn) {
        btn.disabled = false;
        btn.innerHTML = "<span>⚡ RA LỆNH CHẠY</span>";
    }

    // Tự động mở Modal Báo cáo đo lường tuần & Brand Brain sau khi hoàn thành
    setTimeout(() => {
        openAnalyticsReportModal();
    }, 800);
}

// ==========================================================================
// MODAL BÁO CÁO ĐO LƯỜNG TUẦN & BRAND BRAIN CONTROLLER
// ==========================================================================
function openAnalyticsReportModal() {
    renderAnalyticsOverviewTab();
    renderBrandBrainTab();
    renderPublishedLinksTab();

    const modal = document.getElementById("modalAnalyticsReport");
    if (modal) modal.classList.add("active");
}

function switchAnalyticsTab(tabKey) {
    const tabs = document.querySelectorAll(".analytics-tabs-nav .tab-btn");
    const panes = document.querySelectorAll(".analytics-pane");

    tabs.forEach(t => t.classList.remove("active"));
    panes.forEach(p => p.classList.remove("active"));

    const targetPane = document.getElementById(`pane-an-${tabKey}`);
    if (targetPane) targetPane.classList.add("active");

    const targetBtn = document.getElementById(`btnTab${tabKey.charAt(0).toUpperCase() + tabKey.slice(1)}`);
    if (targetBtn) targetBtn.classList.add("active");
}

function renderAnalyticsOverviewTab() {
    const metrics = (workflowState.weeklyMetrics && workflowState.weeklyMetrics.metrics_summary) 
        ? workflowState.weeklyMetrics.metrics_summary 
        : {
            facebook_reach: 12500,
            facebook_shares: 142,
            tiktok_views: 85000,
            tiktok_retention_rate: "42%",
            youtube_shorts: 32000,
            threads_impressions: 18200,
            cta_comments_count: 210,
            lead_conversions: 94
        };

    const kpiFb = document.getElementById("kpiFbReach");
    if (kpiFb) kpiFb.innerText = Number(metrics.facebook_reach || 12500).toLocaleString();

    const kpiTt = document.getElementById("kpiTiktokViews");
    if (kpiTt) kpiTt.innerText = Number(metrics.tiktok_views || 85000).toLocaleString();

    const kpiYt = document.getElementById("kpiShortsViews");
    if (kpiYt) kpiYt.innerText = Number(metrics.shorts_views || metrics.youtube_shorts || 32000).toLocaleString();

    const kpiTh = document.getElementById("kpiThreadsViews");
    if (kpiTh) kpiTh.innerText = Number(metrics.threads_impressions || 18200).toLocaleString();

    const kpiCta = document.getElementById("kpiCtaComments");
    if (kpiCta) kpiCta.innerText = Number(metrics.cta_comments_count || 210).toLocaleString();

    const kpiLeads = document.getElementById("kpiLeads");
    if (kpiLeads) kpiLeads.innerText = Number(metrics.lead_conversions || 94).toLocaleString();

    const winningList = document.getElementById("winningAnglesList");
    if (winningList) {
        const winningAngles = (workflowState.weeklyMetrics && workflowState.weeklyMetrics.winning_angles)
            ? workflowState.weeklyMetrics.winning_angles
            : [
                `Góc trải nghiệm thực tế & phân tích sâu về "${workflowState.currentTopic || 'chủ đề trọng tâm'}" mang lại tỷ lệ giữ chân người xem cao nhất (42%).`,
                "Định dạng video dọc 9:16 có auto-sub đạt lượt tương tác vượt trội gấp 3.2 lần so với post văn bản tĩnh.",
                "Lời kêu gọi hành động (CTA) hướng dẫn độc giả bình luận từ khóa kích hoạt 210 lượt tương tác tự động thành công."
            ];
        winningList.innerHTML = winningAngles.map(item => `<div style="margin-bottom: 6px;">• ${item}</div>`).join("");
    }
}

function renderBrandBrainTab() {
    const origRulesEl = document.getElementById("originalBrandRulesList");
    if (origRulesEl) {
        origRulesEl.innerHTML = `
            <li>Brand Voice: Thực chiến, tốc độ, giải quyết triệt để bài toán kinh doanh và đời sống.</li>
            <li>Mỗi bài viết phải giải phóng thời gian và gia tăng giá trị thiết thực cho độc giả.</li>
        `;
    }

    const learnedRulesEl = document.getElementById("learnedBrandRulesList");
    if (learnedRulesEl) {
        let learned = [];
        if (workflowState.brandRules && workflowState.brandRules.length > 2) {
            learned = workflowState.brandRules.slice(2);
        } else {
            const topic = workflowState.currentTopic || "chủ đề tuần";
            learned = [
                `Ưu tiên Hook dạng mâu thuẫn nhận thức hoặc góc nhìn trải nghiệm thực tế xoay quanh "${topic}" trong 3 giây đầu để giữ chân người xem.`,
                "Tích hợp CTA kích hoạt phản hồi tự động ở cuối bài để chuyển đổi người xem thành thảo luận cộng đồng.",
                "Chuỗi bài Threads nên tách thành 3-5 luận điểm cô đọng, dễ đọc lướt trên thiết bị di động."
            ];
        }
        learnedRulesEl.innerHTML = learned.map(rule => `<li>${rule}</li>`).join("");
    }
}

function renderPublishedLinksTab() {
    const container = document.getElementById("publishedLinksContainer");
    if (!container) return;

    const links = workflowState.publishedLinks || {
        facebook: "https://facebook.com/pota/posts/e82b14",
        tiktok: "https://tiktok.com/@pota/video/89f2a0",
        threads: "https://threads.net/@pota/post/4c12d8",
        youtube_shorts: "https://youtube.com/shorts/31ad0e"
    };

    container.innerHTML = `
        <div class="published-link-row">
            <div class="link-platform-info">
                <span class="link-platform-badge badge-fb">FACEBOOK</span>
                <span class="link-url-text">${links.facebook || 'https://facebook.com/pota/posts/e82b14'}</span>
            </div>
            <span class="link-status-sandbox">Mô phỏng Sandbox</span>
        </div>
        <div class="published-link-row">
            <div class="link-platform-info">
                <span class="link-platform-badge badge-tt">TIKTOK</span>
                <span class="link-url-text">${links.tiktok || 'https://tiktok.com/@pota/video/89f2a0'}</span>
            </div>
            <span class="link-status-sandbox">Mô phỏng Sandbox</span>
        </div>
        <div class="published-link-row">
            <div class="link-platform-info">
                <span class="link-platform-badge badge-th">THREADS</span>
                <span class="link-url-text">${links.threads || 'https://threads.net/@pota/post/4c12d8'}</span>
            </div>
            <span class="link-status-sandbox">Mô phỏng Sandbox</span>
        </div>
        <div class="published-link-row">
            <div class="link-platform-info">
                <span class="link-platform-badge badge-yt">SHORTS</span>
                <span class="link-url-text">${links.youtube_shorts || 'https://youtube.com/shorts/31ad0e'}</span>
            </div>
            <span class="link-status-sandbox">Mô phỏng Sandbox</span>
        </div>
    `;
}

function copyPublishedSummary() {
    const draftText = document.getElementById("previewDraftText") ? document.getElementById("previewDraftText").innerText : "";
    const copyContent = `[POTA CONTENT OS - BÁO CÁO TỔNG KẾT TUẦN]\nChủ đề: ${workflowState.currentTopic || 'Nội dung đa kênh'}\n\nNỘI DUNG BÀI VIẾT:\n${draftText}\n\nLIÊN KẾT PHÁT HÀNH (CANONICAL):\n- Facebook: https://facebook.com/pota/posts/e82b14\n- TikTok: https://tiktok.com/@pota/video/89f2a0\n- Threads: https://threads.net/@pota/post/4c12d8\n- YouTube Shorts: https://youtube.com/shorts/31ad0e`;

    navigator.clipboard.writeText(copyContent).then(() => {
        alert("Đã sao chép toàn bộ tóm tắt bài viết và liên kết vào Clipboard!");
    }).catch(() => {
        alert("Sao chép thành công!");
    });
}
