/* Canvas charts: hex/rgba for broad Chart.js + canvas support; UI tokens stay OKLCH in CSS */
const chartColors = {
    lineBorder: '#0d9488',
    lineFill: 'rgba(13, 148, 136, 0.14)',
    doughnut: ['#0d9488', '#dc2626', '#2563eb', '#d97706']
};

let userChartInstance = null;
let fileChartInstance = null;

(function () {
    const toggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('adminSidebar');
    if (!toggle || !sidebar) return;
    toggle.addEventListener('click', function () {
        const open = sidebar.classList.toggle('is-open');
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
})();

function showTab(name) {
    document.querySelectorAll('.tab-pane').forEach(function (p) { p.classList.remove('active'); });
    var pane = document.getElementById('tab-' + name);
    if (pane) pane.classList.add('active');

    document.querySelectorAll('.sb-nav .nav-item[data-tab]').forEach(function (n) {
        n.classList.toggle('active', n.getAttribute('data-tab') === name);
    });

    if (name === 'stats') loadStats();

    if (window.innerWidth <= 960) {
        var sidebar = document.getElementById('adminSidebar');
        var toggle = document.getElementById('sidebarToggle');
        if (sidebar) sidebar.classList.remove('is-open');
        if (toggle) toggle.setAttribute('aria-expanded', 'false');
    }
}

async function loadStats() {
    try {
        const response = await fetch('/admin/stats_data');
        const data = await response.json();
        const userCtx = document.getElementById('userChart').getContext('2d');
        if (userChartInstance) userChartInstance.destroy();
        userChartInstance = new Chart(userCtx, {
            type: 'line',
            data: {
                labels: data.users.map(function (u) { return u.date; }),
                datasets: [{
                    label: 'Người dùng mới',
                    data: data.users.map(function (u) { return u.count; }),
                    borderColor: chartColors.lineBorder,
                    backgroundColor: chartColors.lineFill,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, ticks: { font: { size: 11 } } },
                    y: { beginAtZero: true, grid: { color: 'rgba(15, 23, 42, 0.08)' }, ticks: { font: { size: 11 } } }
                }
            }
        });
        const fileCtx = document.getElementById('fileChart').getContext('2d');
        if (fileChartInstance) fileChartInstance.destroy();
        fileChartInstance = new Chart(fileCtx, {
            type: 'doughnut',
            data: {
                labels: data.files.map(function (f) { return f.status; }),
                datasets: [{
                    data: data.files.map(function (f) { return f.count; }),
                    backgroundColor: chartColors.doughnut,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '58%',
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } }
                }
            }
        });
    } catch (e) { console.error(e); }
}

function updateRole(userId, newRole) {
    if (!confirm('Thay đổi quyền User #' + userId + ' thành ' + newRole + '?')) return;
    fetch('/admin/update_role', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, new_role: newRole })
    }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.status === 'success') location.reload();
        else alert('Lỗi: ' + d.message);
    });
}

function viewChat(sessionId) {
    document.getElementById('chatModal').classList.add('open');
    document.getElementById('chatContent').innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;"><i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Đang tải...</p>';
    fetch('/admin/get_session_chat/' + sessionId)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            var html = '';
            
            // Render báo cáo ban đầu
            if (data.report) {
                html += '<div style="margin-bottom: 20px; padding: 15px; background: rgba(13, 148, 136, 0.05); border-left: 4px solid var(--admin-accent); border-radius: 4px;">';
                html += '<h4 style="margin-top: 0; margin-bottom: 15px; color: var(--admin-accent); font-size: 1.1rem;"><i class="fas fa-file-alt"></i> Báo cáo phân tích gốc</h4>';
                html += '<div class="markdown-body" style="font-size: 0.95rem;">' + marked.parse(data.report) + '</div>';
                html += '</div>';
            }
            
            // Render lịch sử chat
            if (data.chat && data.chat.length > 0) {
                html += '<h4 style="margin-top: 20px; margin-bottom: 15px; font-size: 1.1rem; color: var(--text); border-bottom: 1px solid var(--border-dark); padding-bottom: 8px;"><i class="fas fa-comments"></i> Lịch sử thảo luận</h4>';
                data.chat.forEach(function (msg) {
                    var isUser = msg.role.toLowerCase() === 'user';
                    var parsedContent = marked.parse(msg.content);
                    html += '<div class="chat-msg ' + (isUser ? 'msg-user' : 'msg-ai') + '">' +
                        '<div class="msg-role"><i class="fas ' + (isUser ? 'fa-user' : 'fa-robot') + '" aria-hidden="true"></i> ' + (isUser ? 'Người dùng' : 'AI Trợ lý') + '</div>' +
                        '<div class="markdown-body" style="font-size: 0.95rem;">' + parsedContent + '</div>' +
                        '<div class="msg-time">' + msg.time + '</div></div>';
                });
            } else if (!data.report) {
                html = '<p style="text-align:center;color:var(--muted);">Không có dữ liệu cho phiên này.</p>';
            }
            
            document.getElementById('chatContent').innerHTML = html;
        })
        .catch(function(e) {
            document.getElementById('chatContent').innerHTML = '<p style="color:var(--admin-danger);text-align:center;">Lỗi khi tải nội dung: ' + e.message + '</p>';
        });
}

function closeModal() { document.getElementById('chatModal').classList.remove('open'); }

function deleteFile(fileId) {
    if (!confirm('Xóa tệp này sẽ xóa toàn bộ báo cáo và phiên chat liên quan?')) return;
    fetch('/admin/delete_file/' + fileId, { method: 'DELETE' })
        .then(function (r) { return r.json(); }).then(function (d) {
            if (d.status === 'success') location.reload();
            else alert(d.message);
        });
}

function toggleSelectAll() {
    var isChecked = document.getElementById('selectAll').checked;
    document.querySelectorAll('.file-checkbox').forEach(function (cb) { cb.checked = isChecked; });
    updateBulkBtn();
}

function updateBulkBtn() {
    var selectedCount = document.querySelectorAll('.file-checkbox:checked').length;
    document.getElementById('bulkDeleteBtn').style.display = selectedCount > 0 ? 'inline-block' : 'none';
}

function bulkDeleteFiles() {
    var selectedIds = Array.from(document.querySelectorAll('.file-checkbox:checked')).map(function (cb) { return cb.value; });
    if (!confirm('Bạn có chắc chắn muốn xóa ' + selectedIds.length + ' tệp tin đã chọn?')) return;

    fetch('/admin/bulk_delete_files', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ file_ids: selectedIds })
    })
        .then(function (r) { return r.json(); })
        .then(function (d) {
            if (d.status === 'success') {
                alert(d.message);
                location.reload();
            } else {
                alert('Lỗi: ' + d.message);
            }
        });
}
