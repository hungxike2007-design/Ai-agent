// ── Circuit / data-stream background ──
(function () {
    const canvas = document.getElementById('circuit-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H;
    const streams = [];
    const N = 30;

    function resize() {
        W = canvas.width = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    function initStreams() {
        streams.length = 0;
        for (let i = 0; i < N; i++) {
            streams.push({
                x: Math.random() * W,
                y: Math.random() * H,
                len: Math.random() * 80 + 40,
                speed: Math.random() * 0.6 + 0.2,
                alpha: Math.random() * 0.12 + 0.04,
                hue: 168 + (Math.random() - 0.5) * 30,
                angle: Math.random() * Math.PI * 2,
            });
        }
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        streams.forEach(s => {
            const dx = Math.cos(s.angle) * s.speed;
            const dy = Math.sin(s.angle) * s.speed;
            s.x += dx; s.y += dy;
            if (s.x < -s.len || s.x > W + s.len || s.y < -s.len || s.y > H + s.len) {
                s.x = Math.random() * W;
                s.y = Math.random() * H;
            }

            const grad = ctx.createLinearGradient(
                s.x, s.y,
                s.x - Math.cos(s.angle) * s.len,
                s.y - Math.sin(s.angle) * s.len
            );
            grad.addColorStop(0, `oklch(58% 0.14 ${s.hue} / ${s.alpha})`);
            grad.addColorStop(1, `oklch(58% 0.14 ${s.hue} / 0)`);

            ctx.beginPath();
            ctx.moveTo(s.x, s.y);
            ctx.lineTo(s.x - Math.cos(s.angle) * s.len, s.y - Math.sin(s.angle) * s.len);
            ctx.strokeStyle = grad;
            ctx.lineWidth = 1.5;
            ctx.stroke();
        });
        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', () => { resize(); initStreams(); });
    resize(); initStreams(); draw();
})();

function checkStrength(val) {
    const fill = document.getElementById('strength-fill');
    if (!fill) return;
    let score = 0;
    if (val.length >= 8) score++;
    if (/[A-Z]/.test(val)) score++;
    if (/[0-9]/.test(val)) score++;
    if (/[^A-Za-z0-9]/.test(val)) score++;
    const widths  = ['0%', '25%', '50%', '75%', '100%'];
    const colors  = ['', 'oklch(52% 0.2 25)', 'oklch(55% 0.18 50)', 'oklch(55% 0.16 90)', 'oklch(52% 0.14 155)'];
    fill.style.width = widths[score];
    fill.style.background = colors[score] || 'transparent';
}

// ── Floating particles (reset_password specific) ──
(function () {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, particles = [];
    const N = 40;

    function resize() { W = canvas.width = window.innerWidth; H = canvas.height = window.innerHeight; }

    function init() {
        particles = Array.from({ length: N }, () => ({
            x: Math.random() * W, y: Math.random() * H,
            r: Math.random() * 3 + 1,
            vx: (Math.random() - 0.5) * 0.4,
            vy: (Math.random() - 0.5) * 0.4,
            alpha: Math.random() * 0.2 + 0.05,
            hue: 250 + Math.random() * 60,
        }));
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        particles.forEach(p => {
            p.x += p.vx; p.y += p.vy;
            if (p.x < 0 || p.x > W) p.vx *= -1;
            if (p.y < 0 || p.y > H) p.vy *= -1;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `oklch(60% 0.15 ${p.hue} / ${p.alpha})`;
            ctx.fill();
        });
        // Lines between nearby
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const d = Math.hypot(particles[i].x - particles[j].x, particles[i].y - particles[j].y);
                if (d < 130) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `oklch(58% 0.14 270 / ${(1 - d / 130) * 0.12})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(draw);
    }

    window.addEventListener('resize', () => { resize(); init(); });
    resize(); init(); draw();
})();
