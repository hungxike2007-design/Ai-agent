// ── Soft particle background for public report ──
(function () {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, pts = [];
    function resize() { 
        W = canvas.width = window.innerWidth; 
        H = canvas.height = window.innerHeight; 
    }
    function init() {
        pts = Array.from({ length: 30 }, () => ({
            x: Math.random() * W, y: Math.random() * H,
            vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25,
            r: Math.random() * 2 + 1,
            hue: 160 + Math.random() * 20,
            a: Math.random() * .12 + .04,
        }));
    }
    function draw() {
        ctx.clearRect(0, 0, W, H);
        pts.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > W) p.vx *= -1;
            if (p.y < 0 || p.y > H) p.vy *= -1;
            ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `oklch(55% 0.13 ${p.hue} / ${p.a})`; ctx.fill();
        });
        for (let i = 0; i < pts.length; i++) {
            for (let j = i + 1; j < pts.length; j++) {
                const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
                if (d < 120) {
                    ctx.beginPath(); ctx.moveTo(pts[i].x, pts[i].y); ctx.lineTo(pts[j].x, pts[j].y);
                    ctx.strokeStyle = `oklch(52% 0.12 168 / ${(1 - d / 120) * .08})`; ctx.lineWidth = 1; ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }
    window.addEventListener('resize', () => { resize(); init(); });
    resize(); init(); draw();
})();
