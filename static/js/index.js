function switchTab(type) {
    const isLogin = type === 'login';
    document.getElementById('login-tab').classList.toggle('active', isLogin);
    document.getElementById('register-tab').classList.toggle('active', !isLogin);
    document.getElementById('login-tab').setAttribute('aria-selected', isLogin);
    document.getElementById('register-tab').setAttribute('aria-selected', !isLogin);
    document.getElementById('login-form').classList.toggle('d-none', !isLogin);
    document.getElementById('register-form').classList.toggle('d-none', isLogin);
}

// ── Neural network particle animation ──
(function () {
    const canvas = document.getElementById('neural-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, nodes = [], animId;
    const N_NODES = 55;
    const MAX_DIST = 160;
    const BRAND_H = 168; // OKLCH hue

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    function oklchToCss(l, c, h, a) {
        return `oklch(${l}% ${c} ${h} / ${a})`;
    }

    function init() {
        nodes = Array.from({ length: N_NODES }, () => ({
            x: Math.random() * W,
            y: Math.random() * H,
            vx: (Math.random() - 0.5) * 0.35,
            vy: (Math.random() - 0.5) * 0.35,
            r: Math.random() * 2.5 + 1.5,
            pulse: Math.random() * Math.PI * 2,
        }));
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);

        // Update & draw nodes
        nodes.forEach(n => {
            n.x += n.vx; n.y += n.vy;
            n.pulse += 0.02;
            if (n.x < 0 || n.x > W) n.vx *= -1;
            if (n.y < 0 || n.y > H) n.vy *= -1;

            const alpha = 0.5 + 0.25 * Math.sin(n.pulse);
            ctx.beginPath();
            ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
            ctx.fillStyle = oklchToCss(60, 0.14, BRAND_H, alpha);
            ctx.fill();
        });

        // Draw edges
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const a = nodes[i], b = nodes[j];
                const d = Math.hypot(a.x - b.x, a.y - b.y);
                if (d < MAX_DIST) {
                    const alpha = (1 - d / MAX_DIST) * 0.18;
                    ctx.beginPath();
                    ctx.moveTo(a.x, a.y);
                    ctx.lineTo(b.x, b.y);
                    ctx.strokeStyle = oklchToCss(58, 0.13, BRAND_H, alpha);
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }

        animId = requestAnimationFrame(draw);
    }

    window.addEventListener('resize', () => { resize(); init(); });
    resize(); init(); draw();
})();
