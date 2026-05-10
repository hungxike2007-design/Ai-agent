const PROMPTS = {
    analyst: 'Bạn là chuyên gia phân tích dữ liệu hàng đầu. Hãy trả lời bằng tiếng Việt, chuyên nghiệp, kèm số liệu cụ thể và đề xuất hành động rõ ràng.',
    concise: 'Bạn là trợ lý AI phân tích dữ liệu. Trả lời ngắn gọn, súc tích bằng tiếng Việt. Tóm tắt điểm chính trong tối đa 3 bullet point.',
    detailed: 'Bạn là chuyên gia phân tích dữ liệu. Cung cấp phân tích sâu bằng tiếng Việt: bối cảnh, xu hướng, bất thường, nguyên nhân và đề xuất cụ thể kèm ưu tiên thực hiện.',
    vi: 'Bạn là trợ lý AI thông minh. LUÔN LUÔN trả lời bằng tiếng Việt thuần túy, dễ hiểu. Không dùng tiếng Anh trong câu trả lời trừ tên kỹ thuật bắt buộc.',
};

function setPrompt(key) {
    document.getElementById('system-prompt').value = PROMPTS[key] || '';
}

// ── Animated AI nodes on canvas ──
(function () {
    const canvas = document.getElementById('ai-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, nodes = [];
    function resize() { 
        W = canvas.width = window.innerWidth; 
        H = canvas.height = window.innerHeight; 
    }
    function init() {
        nodes = Array.from({ length: 40 }, () => ({
            x: Math.random() * W, y: Math.random() * H,
            vx: (Math.random() - .5) * .3, vy: (Math.random() - .5) * .3,
            r: Math.random() * 2 + 1, pulse: Math.random() * Math.PI * 2,
        }));
    }
    function draw() {
        ctx.clearRect(0, 0, W, H);
        nodes.forEach(n => {
            n.x += n.vx; n.y += n.vy; n.pulse += .018;
            if (n.x < 0 || n.x > W) n.vx *= -1;
            if (n.y < 0 || n.y > H) n.vy *= -1;
            const a = .4 + .2 * Math.sin(n.pulse);
            ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
            ctx.fillStyle = `oklch(58% 0.13 168 / ${a})`; ctx.fill();
        });
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const d = Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y);
                if (d < 140) {
                    ctx.beginPath(); ctx.moveTo(nodes[i].x, nodes[i].y); ctx.lineTo(nodes[j].x, nodes[j].y);
                    ctx.strokeStyle = `oklch(55% 0.12 168 / ${(1 - d / 140) * .12})`; ctx.lineWidth = 1; ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    window.addEventListener('resize', () => { resize(); init(); });
    resize(); init(); draw();
})();
