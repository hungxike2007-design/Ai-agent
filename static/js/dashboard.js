// Dashboard Logic
const chatBox = document.getElementById('chatBox');
const chatContent = document.getElementById('chat-content');
const questionInput = document.getElementById('userQuestion');
const loading = document.getElementById('ai-loading');
const btnAsk = document.getElementById('btnAsk');

// Lấy session ID ban đầu từ config
let currentSessionId = window.DASHBOARD_CONFIG.currentSessionId;

function showShareModal() {
    if (!currentSessionId) return alert("Chưa có phiên chat nào được chọn!");
    fetch(`/ai/share_session/${currentSessionId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.share_url) {
                document.getElementById('shareLinkInput').value = window.location.origin + data.share_url;
                document.getElementById('shareModal').classList.add('active');
            } else { alert("Lỗi: " + (data.error || "Không thể tạo link chia sẻ")); }
        });
}

function closeShareModal() { 
    document.getElementById('shareModal').classList.remove('active'); 
}

function copyShareLink() {
    const input = document.getElementById('shareLinkInput');
    input.select(); 
    document.execCommand('copy');
    alert("Đã copy link!");
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('closed');
}

// Đếm và hiển thị số dòng / cột của bảng
function updateRowCount() {
    const wrap = document.getElementById('excel-table-content');
    const label = document.getElementById('rowCountLabel');
    const info = document.getElementById('tableInfo');
    if (!wrap || !label) return;
    const rows = wrap.querySelectorAll('tbody tr');
    const cols = wrap.querySelectorAll('thead th, tr:first-child th');
    if (rows.length > 0) {
        label.textContent = `Hiển thị ${rows.length} dòng · ${cols.length} cột`;
        if (info) info.style.display = 'block';
    }
}

function toggleHints() {
    const btn = document.getElementById('hintsToggle');
    const body = document.getElementById('hintsBody');
    btn.classList.toggle('open');
    body.classList.toggle('open');
}

async function loadChatSession(sessionId) {
    const dataSection = document.getElementById('data-section');
    const chatSection = document.getElementById('chat-section');
    const tableDiv = document.getElementById('excel-table-content');
    const chartBoxEl = document.getElementById('chart-content');
    const tableInfo = document.getElementById('tableInfo');

    if (dataSection) dataSection.style.display = 'block';
    if (chatSection) chatSection.style.display = 'flex';
    if (tableInfo) tableInfo.style.display = 'none';

    if (tableDiv) tableDiv.innerHTML = '<div class="p-4 text-center text-muted"><i class="fas fa-spinner fa-spin"></i> Đang nạp bảng dữ liệu...</div>';
    if (chartBoxEl) chartBoxEl.style.display = 'none';

    chatContent.innerHTML = '<div style="text-align:center;color:var(--muted);padding:40px;"><i class="fas fa-spinner fa-spin fa-2x"></i><br><br>Đang đồng bộ hội thoại...</div>';

    try {
        const res = await fetch(`${window.DASHBOARD_CONFIG.getSessionUrlBase}/${sessionId}`);
        const contentType = res.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
            throw new Error("Server không trả về dữ liệu JSON.");
        }

        const data = await res.json();
        if (data.error) {
            chatContent.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
            return;
        }

        currentSessionId = sessionId;

        const btnWord = document.querySelector('.btn-word');
        const btnPdf = document.querySelector('.btn-export');
        const btnExcel = document.querySelector('.btn-excel');
        if (btnWord) btnWord.href = `${window.DASHBOARD_CONFIG.exportReportUrl}?format=word&session_id=${sessionId}`;
        if (btnPdf) btnPdf.href = `${window.DASHBOARD_CONFIG.exportReportUrl}?format=pdf&session_id=${sessionId}`;
        if (btnExcel) btnExcel.href = `${window.DASHBOARD_CONFIG.exportExcelUrl}?session_id=${sessionId}`;

        if (tableDiv && data.table_html) {
            tableDiv.innerHTML = data.table_html;
            if (tableInfo) tableInfo.style.display = 'block';
            updateRowCount();
        }

        if (chartBoxEl) {
            if (data.chart_path || data.plotly_json) {
                chartBoxEl.style.display = 'block';
                const grid = document.querySelector('.charts-grid');

                let imagesHtml = '';
                if (data.chart_path) {
                    imagesHtml += `<div class="chart-card"><img src="${data.chart_path}" alt="Biểu đồ" onclick="openLightbox(this.src)"></div>`;
                }

                grid.innerHTML = imagesHtml + `<div id="plotly-chart" class="chart-card" style="${data.plotly_json ? '' : 'display:none;'} min-height:500px; background:#0f172a;"></div>`;

                if (data.plotly_json) {
                    const plotData = JSON.parse(data.plotly_json);
                    Plotly.newPlot('plotly-chart', plotData.data, plotData.layout, { responsive: true, displayModeBar: false });
                }
            } else {
                chartBoxEl.style.display = 'none';
            }
        }

        chatContent.innerHTML = '';
        if (data.messages && data.messages.length > 0) {
            data.messages.forEach(msg => {
                const isAI = msg.role.toLowerCase() === 'assistant' || msg.role.toLowerCase() === 'ai';
                const body = isAI ? `<div class="md-body">${marked.parse(msg.content)}</div>` : msg.content;
                chatContent.innerHTML += `
                    <div class="bubble ${isAI ? 'ai-bubble' : 'user-bubble'}" ${isAI ? 'style="max-width:100%"' : ''}>
                        <strong><i class="fas ${isAI ? 'fa-robot' : 'fa-user'}"></i> ${isAI ? 'AI Agent' : 'Bạn'}</strong>
                        ${body}
                    </div>`;
            });
        } else {
            chatContent.innerHTML = '<p style="color:var(--muted);font-size:.85rem;text-align:center;padding:20px;">Phiên này chưa có tin nhắn.</p>';
        }

        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;

    } catch (err) {
        chatContent.innerHTML = `<div class="alert alert-danger">Lỗi kết nối: ${err}</div>`;
    }
}

function fillChat(text) {
    const input = document.getElementById('userQuestion');
    input.value = text;
    input.focus();
}

async function askAI() {
    const question = questionInput.value.trim();
    const modelChoice = document.getElementById('aiModelSelect').value;
    if (!question) return;
    chatContent.innerHTML += `<div class="bubble user-bubble"><strong><i class="fas fa-user"></i> Bạn</strong>${question}</div>`;
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
    questionInput.value = '';
    loading.style.display = 'flex';
    btnAsk.disabled = true;

    try {
        const res = await fetch(window.DASHBOARD_CONFIG.askUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, model: modelChoice })
        });
        const data = await res.json();
        chatContent.innerHTML += `<div class="bubble ai-bubble" style="max-width:100%"><strong><i class="fas fa-robot"></i> AI Agent</strong><div class="md-body">${marked.parse(data.answer)}</div></div>`;
        if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
        loadSidebarHistory();
    } catch (e) { alert('Lỗi kết nối server!'); }
    finally { loading.style.display = 'none'; btnAsk.disabled = false; }
}

async function loadSidebarHistory() {
    const list = document.getElementById('historyList');
    if (!list) return;
    try {
        const res = await fetch(window.DASHBOARD_CONFIG.historyUrl);
        const data = await res.json();
        list.innerHTML = data.map(item => `
            <div class="hist-item" id="item-${item.id}" onclick="handleHistItemClick(event, ${item.id})">
                <div class="hist-info">
                    <input type="checkbox" class="hist-checkbox" value="${item.id}" onclick="updateBulkCount(event)">
                    <i class="fas fa-message"></i>
                    <span class="hist-title" id="title-${item.id}">${item.title}</span>
                </div>
                <div style="position:relative;">
                    <button class="opts-btn" onclick="toggleMenu(event,${item.id})"><i class="fas fa-ellipsis-vertical"></i></button>
                    <div id="drop-${item.id}" class="drop-menu">
                        <span class="drop-item" onclick="handleRename(event,${item.id})"><i class="fas fa-pen"></i> Đổi tên</span>
                        <span class="drop-item" onclick="handleShare(event,${item.id})"><i class="fas fa-share-nodes"></i> Chia sẻ</span>
                        <span class="drop-item danger" onclick="handleDelete(event,${item.id})"><i class="fas fa-trash"></i> Xóa</span>
                    </div>
                </div>
            </div>`).join('');
    } catch (e) { console.error(e); }
}

function toggleMenu(event, id) {
    event.stopPropagation();
    document.querySelectorAll('.drop-menu').forEach(el => { if (el.id !== `drop-${id}`) el.classList.remove('open'); });
    document.getElementById(`drop-${id}`).classList.toggle('open');
}

async function handleRename(event, id) {
    event.stopPropagation();
    const dropMenu = document.getElementById(`drop-${id}`);
    if (dropMenu) dropMenu.classList.remove('open');

    const old = document.getElementById(`title-${id}`).innerText;
    const input = document.getElementById('renameInput');
    input.value = old;

    openInlineAlert('renameAlert');
    setTimeout(() => { input.focus(); input.select(); }, 150);

    // Set up confirm handler
    const confirmBtn = document.getElementById('renameConfirmBtn');
    const newHandler = async () => {
        const newTitle = input.value.trim();
        if (!newTitle || newTitle === old) {
            closeInlineAlert('renameAlert');
            return;
        }
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';
        try {
            const res = await fetch(`/ai/rename_session/${id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_title: newTitle }) });
            if ((await res.json()).success) {
                document.getElementById(`title-${id}`).innerText = newTitle;
                closeInlineAlert('renameAlert');
                showToast('success', '<i class="fas fa-check-circle"></i> Đã đổi tên thành công!');
            }
        } catch (e) {
            showToast('error', '<i class="fas fa-exclamation-circle"></i> Lỗi kết nối server!');
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-check"></i> Lưu';
        }
    };
    confirmBtn.onclick = newHandler;
    // Also allow Enter key in input
    input.onkeydown = (e) => { if (e.key === 'Enter') newHandler(); };
}

async function handleShare(event, id) {
    event.stopPropagation();
    const dropMenu = document.getElementById(`drop-${id}`);
    if (dropMenu) dropMenu.classList.remove('open');

    const linkInput = document.getElementById('shareAlertLink');
    const copyBtn = document.getElementById('shareAlertCopyBtn');
    linkInput.value = 'Đang tạo link chia sẻ...';
    copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
    copyBtn.classList.remove('copied');

    openInlineAlert('shareAlert');

    try {
        const res = await fetch(`/ai/share_session/${id}`, { method: 'POST' });
        const data = await res.json();
        if (data.share_url) {
            linkInput.value = window.location.origin + data.share_url;
        } else {
            linkInput.value = 'Lỗi: không thể tạo link';
            showToast('error', '<i class="fas fa-exclamation-circle"></i> ' + (data.error || 'Không thể tạo link chia sẻ'));
        }
    } catch (e) {
        linkInput.value = 'Lỗi kết nối server';
        showToast('error', '<i class="fas fa-exclamation-circle"></i> Lỗi kết nối server!');
    }
}

async function handleDelete(event, id) {
    event.stopPropagation();
    const dropMenu = document.getElementById(`drop-${id}`);
    if (dropMenu) dropMenu.classList.remove('open');

    openInlineAlert('deleteAlert');

    const confirmBtn = document.getElementById('deleteConfirmBtn');
    confirmBtn.onclick = async () => {
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xóa...';

        const item = document.getElementById(`item-${id}`);
        if (item) item.style.opacity = '0.4';

        try {
            const res = await fetch(`/ai/delete_session/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                closeInlineAlert('deleteAlert');
                if (item) {
                    item.style.transition = 'all 0.3s ease';
                    item.style.transform = 'translateX(-100%)';
                    item.style.opacity = '0';
                    setTimeout(() => item.remove(), 300);
                }
                if (currentSessionId == id) {
                    currentSessionId = "";
                    document.getElementById('data-section').style.display = 'none';
                    document.getElementById('chat-section').style.display = 'none';
                }
                showToast('success', '<i class="fas fa-check-circle"></i> Đã xóa phiên chat thành công!');
            } else {
                if (item) item.style.opacity = '1';
                showToast('error', '<i class="fas fa-exclamation-circle"></i> ' + (data.error || 'Lỗi khi xóa phiên chat.'));
            }
        } catch (e) {
            if (item) item.style.opacity = '1';
            showToast('error', '<i class="fas fa-exclamation-circle"></i> Lỗi kết nối server: ' + e.message);
        } finally {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = '<i class="fas fa-trash"></i> Xóa vĩnh viễn';
        }
    };
}

// ===== INLINE ALERT UTILITIES =====
function openInlineAlert(id) {
    const overlay = document.getElementById(id);
    if (overlay) overlay.classList.add('active');
}

function closeInlineAlert(id) {
    const overlay = document.getElementById(id);
    if (overlay) overlay.classList.remove('active');
}

function showToast(type, html) {
    const toast = document.createElement('div');
    toast.className = `inline-toast ${type}`;
    toast.innerHTML = html;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.transition = 'opacity .3s ease';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function copyShareAlertLink() {
    const input = document.getElementById('shareAlertLink');
    const btn = document.getElementById('shareAlertCopyBtn');
    if (!input.value || input.value.startsWith('Đang') || input.value.startsWith('Lỗi')) return;

    navigator.clipboard.writeText(input.value).then(() => {
        btn.innerHTML = '<i class="fas fa-check"></i> Đã copy!';
        btn.classList.add('copied');
        showToast('success', '<i class="fas fa-check-circle"></i> Đã copy link vào clipboard!');
        setTimeout(() => {
            btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
            btn.classList.remove('copied');
        }, 2500);
    }).catch(() => {
        // Fallback for older browsers
        input.select();
        document.execCommand('copy');
        btn.innerHTML = '<i class="fas fa-check"></i> Đã copy!';
        btn.classList.add('copied');
    });
}


// BULK DELETE LOGIC
let isBulkMode = false;

function toggleBulkMode() {
    isBulkMode = !isBulkMode;
    const list = document.getElementById('historyList');
    const opts = document.getElementById('bulkOpts');
    const btn = document.getElementById('bulkToggleBtn');

    if (isBulkMode) {
        list.classList.add('bulk-mode');
        opts.classList.add('active');
        btn.style.color = 'var(--green)';
        btn.style.borderColor = 'var(--green)';
    } else {
        list.classList.remove('bulk-mode');
        opts.classList.remove('active');
        btn.style.color = '';
        btn.style.borderColor = '';
        document.querySelectorAll('.hist-checkbox').forEach(cb => cb.checked = false);
        updateBulkCount();
    }
}

function handleHistItemClick(event, id) {
    if (isBulkMode) {
        if (event.target.tagName !== 'INPUT') {
            const cb = document.querySelector(`#item-${id} .hist-checkbox`);
            if (cb) { cb.checked = !cb.checked; updateBulkCount(); }
        }
    } else {
        loadChatSession(id);
    }
}

function updateBulkCount(event) {
    if (event) event.stopPropagation();
    const count = document.querySelectorAll('.hist-checkbox:checked').length;
    document.getElementById('bulkCount').innerText = `${count} đã chọn`;
}

async function executeBulkDelete() {
    const checkboxes = document.querySelectorAll('.hist-checkbox:checked');
    const selectedIds = Array.from(checkboxes).map(cb => parseInt(cb.value));

    if (selectedIds.length === 0) {
        alert('Vui lòng chọn ít nhất một phiên chat để xóa!');
        return;
    }

    if (confirm(`Bạn có chắc muốn xóa ${selectedIds.length} phiên chat đã chọn?`)) {
        try {
            const res = await fetch('/ai/bulk_delete_sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_ids: selectedIds })
            });
            const data = await res.json();
            if (data.success) {
                location.reload();
            } else {
                alert(data.error || "Lỗi xóa dữ liệu");
            }
        } catch (e) {
            alert('Lỗi kết nối server: ' + e.message);
        }
    }
}

// FEEDBACK STARS
let selectedStar = 0;
const starLabels = ['', 'Rất tệ 😞', 'Tệ 😕', 'Bình thường 😐', 'Tốt 😊', 'Xuất sắc 🤩'];

function setStar(n) {
    selectedStar = n;
    document.querySelectorAll('.fb-star').forEach((btn, i) => {
        btn.classList.toggle('active', i < n);
        btn.style.color = i < n ? '#f59e0b' : '#e2e8f0';
    });
    document.getElementById('starLabel').textContent = starLabels[n] || '';
}

function openFeedbackModal() {
    selectedStar = 0;
    document.querySelectorAll('.fb-star').forEach(btn => {
        btn.classList.remove('active');
        btn.style.color = '#e2e8f0';
    });
    document.getElementById('starLabel').textContent = '';
    document.getElementById('feedbackComment').value = '';
    document.getElementById('feedbackCategory').value = 'Chất lượng phân tích';
    document.getElementById('feedbackModal').classList.add('active');
}

function closeFeedbackModal() {
    document.getElementById('feedbackModal').classList.remove('active');
}

async function submitFeedback() {
    if (!selectedStar) {
        document.getElementById('starLabel').textContent = '⚠️ Vui lòng chọn số sao!';
        document.getElementById('starLabel').style.color = '#ef4444';
        return;
    }
    const btn = document.getElementById('btnSubmitFeedback');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang gửi...';

    try {
        const res = await fetch('/ai/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rating: selectedStar,
                comment: document.getElementById('feedbackComment').value.trim(),
                category: document.getElementById('feedbackCategory').value,
                session_id: currentSessionId || null
            })
        });
        const data = await res.json();
        if (data.success) {
            closeFeedbackModal();
            const toast = document.createElement('div');
            toast.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
            toast.style.cssText = 'position:fixed;bottom:28px;right:28px;background:linear-gradient(135deg,#059669,#047857);color:#fff;padding:14px 22px;border-radius:14px;font-weight:600;font-size:.9rem;z-index:9999;box-shadow:0 8px 24px rgba(5,150,105,.3);display:flex;align-items:center;gap:10px;animation:slideUp .3s ease';
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        } else {
            alert('Lỗi: ' + data.error);
        }
    } catch (e) {
        alert('Lỗi kết nối server!');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Gửi phản hồi';
    }
}

function openLightbox(src) {
    const modal = document.getElementById('lightboxModal');
    const img = document.getElementById('lightboxImg');
    img.src = src;
    modal.style.display = 'flex';
}

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    updateRowCount();
    loadSidebarHistory();
    
    // Kiểm tra nếu có session_id trong hash (ví dụ #session_123) để tự động load
    const hash = window.location.hash;
    if (hash && hash.startsWith('#session_')) {
        const sid = hash.replace('#session_', '');
        loadChatSession(sid);
        // Xóa hash để tránh load lại khi F5 (tùy chọn)
        // window.history.replaceState(null, null, ' ');
    }

    document.addEventListener('click', () => {
        document.querySelectorAll('.drop-menu').forEach(el => el.classList.remove('open'));
    });
    if (questionInput) {
        questionInput.addEventListener('keypress', e => { if (e.key === 'Enter') askAI(); });
    }

    // Close inline alerts when clicking the overlay background
    document.querySelectorAll('.inline-alert-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.classList.remove('active');
        });
    });

    // Close inline alerts with Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.inline-alert-overlay.active').forEach(overlay => {
                overlay.classList.remove('active');
            });
        }
    });
});
