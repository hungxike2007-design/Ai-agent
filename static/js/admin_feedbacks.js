document.addEventListener('DOMContentLoaded', function() {
    const config = window.FEEDBACK_CONFIG || {};

    if (config.showChart && config.byCategory) {
        const catCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: config.byCategoryLabels,
                datasets: [{ 
                    data: config.byCategoryValues,
                    backgroundColor: ['oklch(52% 0.14 155)','oklch(52% 0.14 250)','oklch(62% 0.16 75)','oklch(52% 0.2 25)','oklch(52% 0.18 285)','oklch(58% 0.17 168)'],
                    borderWidth: 0, 
                    hoverOffset: 6 
                }]
            },
            options: { 
                cutout: '65%', 
                plugins: { 
                    legend: { 
                        position: 'right', 
                        labels: { 
                            font: { family: 'Plus Jakarta Sans', size: 12 }, 
                            boxWidth: 12 
                        } 
                    } 
                } 
            }
        });
    }
});

function openUpdateModal(id, status, note) {
    document.getElementById('currentFeedbackId').value = id;
    document.getElementById('statusSelect').value = status;
    document.getElementById('adminNoteInput').value = note;
    document.getElementById('updateModal').classList.add('open');
}

function closeModal() { 
    document.getElementById('updateModal').classList.remove('open'); 
}

async function saveUpdate() {
    const id = document.getElementById('currentFeedbackId').value;
    const status = document.getElementById('statusSelect').value;
    const note = document.getElementById('adminNoteInput').value.trim();
    const res = await fetch(`/admin/feedback/update/${id}`, { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ status, admin_note: note }) 
    });
    const data = await res.json();
    if (data.status === 'success') { 
        closeModal(); 
        location.reload(); 
    } else {
        alert('Lỗi: ' + data.message);
    }
}

function deleteFeedback(id, btn) {
    const cell = btn.closest('td');
    if (cell.querySelector('.inline-confirm')) return;
    
    // Ẩn các nút hiện tại
    Array.from(cell.children).forEach(child => child.style.display = 'none');
    
    // Tạo callout
    const callout = document.createElement('div');
    callout.className = 'inline-confirm';
    callout.style.cssText = 'background: #fef2f2; border: 1px solid #f87171; padding: 4px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 8px; animation: fadeIn 0.2s ease;';
    
    callout.innerHTML = `
        <span style="font-size: 0.8rem; color: #b91c1c; font-weight: 600;"><i class="fas fa-triangle-exclamation"></i> Chắc chắn xóa?</span>
        <button onclick="executeDelete(${id})" class="btn-sm" style="background: #ef4444; color: white; padding: 2px 8px; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; display: inline-block;">Có</button>
        <button onclick="cancelDelete(this)" class="btn-sm" style="background: #e5e7eb; color: #374151; padding: 2px 8px; border: none; border-radius: 4px; font-weight: 600; cursor: pointer; display: inline-block;">Hủy</button>
    `;
    
    cell.appendChild(callout);
}

function cancelDelete(cancelBtn) {
    const cell = cancelBtn.closest('td');
    const callout = cell.querySelector('.inline-confirm');
    if (callout) callout.remove();
    
    // Hiện lại các nút gốc
    Array.from(cell.children).forEach(child => child.style.display = '');
}

async function executeDelete(id) {
    const res = await fetch(`/admin/feedback/delete/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') { 
        const r = document.getElementById(`row-${id}`); 
        if (r) r.remove(); 
    } else {
        alert('Lỗi: ' + data.message);
    }
}
