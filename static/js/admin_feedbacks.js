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

async function deleteFeedback(id) {
    if (!confirm('Xóa phản hồi này?')) return;
    const res = await fetch(`/admin/feedback/delete/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.status === 'success') { 
        const r = document.getElementById(`row-${id}`); 
        if (r) r.remove(); 
    } else {
        alert('Lỗi: ' + data.message);
    }
}
