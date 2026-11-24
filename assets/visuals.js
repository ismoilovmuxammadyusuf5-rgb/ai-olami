'use strict';
        function getBrandLogoSVG(name) {
            const n = name.toLowerCase();
            // OpenAI / ChatGPT / Sora / Whisper / DALL-E
            if (n.includes('chatgpt') || n.includes('sora') || n.includes('dall-e') || n.includes('whisper')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#10a37f"/><g fill="none" stroke="#fff" stroke-width="1.9" stroke-linecap="round"><path d="M18 8.5c2.8 0 5.1 2 5.5 4.7a5.5 5.5 0 0 1 3.7 7.6 5.5 5.5 0 0 1-5.2 7.2 5.5 5.5 0 0 1-8.5-1.6 5.5 5.5 0 0 1-4.7-7.1 5.5 5.5 0 0 1 4.2-7.8A5.5 5.5 0 0 1 18 8.5Z"/><circle cx="18" cy="18" r="3.2"/></g></svg>`;
            }
            // Google Gemini / Veo / NotebookLM / AlphaFold / GNoME
            if (n.includes('gemini') || n.includes('veo') || n.includes('notebooklm') || n.includes('alphafold') || n.includes('gnome')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><defs><linearGradient id="gemGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#4285f4"/><stop offset="50%" stop-color="#9b72cb"/><stop offset="100%" stop-color="#d96570"/></linearGradient></defs><rect width="36" height="36" rx="10" fill="#0f172a"/><path d="M18 5.5c0 6.9 5.6 12.5 12.5 12.5-6.9 0-12.5 5.6-12.5 12.5 0-6.9-5.6-12.5-12.5-12.5C12.4 18 18 12.4 18 5.5Z" fill="url(#gemGrad)"/></svg>`;
            }
            // Anthropic Claude
            if (n.includes('claude') || n.includes('cline')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#d97757"/><g stroke="#fff" stroke-width="2.3" stroke-linecap="round"><path d="M18 7.5v21M7.5 18h21M10.6 10.6l14.8 14.8M25.4 10.6L10.6 25.4M13.8 8.5l8.4 19M22.2 8.5l-8.4 19M8.5 13.8l19 8.4M8.5 22.2l19-8.4"/></g></svg>`;
            }
            // DeepSeek
            if (n.includes('deepseek')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#1d4ed8"/><path d="M8 20.5c2.2-5.8 8.5-8.5 14.5-6.5 2.5.8 4.2 2.4 5.5 4.2-1.8.8-3.2 2.2-3.8 4-2.5 3.8-8.2 5.3-13.2 2.8-1.5-.8-2.4-2.2-3-4.5Z" fill="#60a5fa"/><path d="M23.5 14l4.5-3.2-1.2 5.2Z" fill="#93c5fd"/><circle cx="13.5" cy="18.2" r="1.5" fill="#0f172a"/></svg>`;
            }
            // Midjourney
            if (n.includes('midjourney')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#0b1120"/><path d="M18 7.5c4.5 4.2 6.8 9.2 6.8 14.5H18V7.5Z" fill="#38bdf8"/><path d="M16.5 10.5c-3.8 3.5-5.8 7.5-5.8 11.5h5.8V10.5Z" fill="#e879f9"/><path d="M7.5 24.5c3.5 2.2 17.5 2.2 21 0l-2.2 3.2H9.7l-2.2-3.2Z" fill="#f8fafc"/></svg>`;
            }
            // xAI Grok
            if (n.includes('grok')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#09090b"/><path d="M10 10l16 16M26 10L10 26" stroke="#fff" stroke-width="2.8" stroke-linecap="round"/><circle cx="18" cy="18" r="8.5" fill="none" stroke="#fff" stroke-width="1.8"/></svg>`;
            }
            // Microsoft Copilot / AutoGen
            if (n.includes('copilot') || n.includes('microsoft')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#1e293b"/><rect x="9" y="9" width="8" height="8" rx="1.8" fill="#f25022"/><rect x="19" y="9" width="8" height="8" rx="1.8" fill="#7fba00"/><rect x="9" y="19" width="8" height="8" rx="1.8" fill="#00a4ef"/><rect x="19" y="19" width="8" height="8" rx="1.8" fill="#ffb900"/></svg>`;
            }
            // Meta Llama / AudioCraft / MusicGen
            if (n.includes('llama') || n.includes('meta') || n.includes('musicgen') || n.includes('audiocraft')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#0668E1"/><path d="M11.5 22.5c-2.5 0-4.2-1.8-4.2-4.3 0-2.8 2.1-5.2 4.7-5.2 2.2 0 3.9 1.5 6 4.7 2.1-3.2 3.8-4.7 6-4.7 2.6 0 4.7 2.4 4.7 5.2 0 2.5-1.7 4.3-4.2 4.3-2.1 0-3.7-1.4-6.5-5.3-2.8 3.9-4.4 5.3-6.5 5.3Z" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round"/></svg>`;
            }
            // Alibaba Qwen / Wan
            if (n.includes('qwen') || n.includes('wan 2.1')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#6366f1"/><polygon points="18,7 27.5,12.5 27.5,23.5 18,29 8.5,23.5 8.5,12.5" fill="none" stroke="#fff" stroke-width="2.2"/><circle cx="18" cy="18" r="4" fill="#fff"/></svg>`;
            }
            // Mistral / Codestral
            if (n.includes('mistral') || n.includes('codestral')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#18181b"/><rect x="8" y="9" width="4" height="4" fill="#ffd800"/><rect x="24" y="9" width="4" height="4" fill="#ffd800"/><rect x="8" y="13.5" width="8" height="4" fill="#ffaf00"/><rect x="20" y="13.5" width="8" height="4" fill="#ffaf00"/><rect x="8" y="18" width="20" height="4" fill="#ff8205"/><rect x="8" y="22.5" width="4" height="4.5" fill="#fa500f"/><rect x="16" y="22.5" width="4" height="4.5" fill="#fa500f"/><rect x="24" y="22.5" width="4" height="4.5" fill="#fa500f"/></svg>`;
            }
            // FLUX / Black Forest Labs
            if (n.includes('flux')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#111827"/><path d="M18 8l10 18H8L18 8Z" fill="none" stroke="#f43f5e" stroke-width="2.4" stroke-linejoin="round"/><path d="M13 21h10" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round"/></svg>`;
            }
            // Runway
            if (n.includes('runway')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#10b981"/><path d="M12 26V10h7.5a5 5 0 0 1 0 10H12m6.5 0L24 26" fill="none" stroke="#042f2e" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
            }
            // Kling AI
            if (n.includes('kling')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#0284c7"/><path d="M12 9v18M24 9l-9 9 9 9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
            }
            // Luma Dream Machine / Genie
            if (n.includes('luma')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#0f172a"/><polygon points="18,7 27,13 27,23 18,29 9,23 9,13" fill="#38bdf8" opacity="0.85"/><polygon points="18,7 27,13 18,18 9,13" fill="#bae6fd"/></svg>`;
            }
            // HeyGen / Synthesia
            if (n.includes('heygen') || n.includes('synthesia')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#7c3aed"/><circle cx="18" cy="14" r="4.5" fill="#fff"/><path d="M10 27c1.5-4.5 14.5-4.5 16 0" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round"/></svg>`;
            }
            // Suno / Udio
            if (n.includes('suno') || n.includes('udio')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#f59e0b"/><circle cx="18" cy="18" r="8" fill="none" stroke="#fff" stroke-width="2.4"/><path d="M15 14l8 4-8 4v-8Z" fill="#fff"/></svg>`;
            }
            // ElevenLabs
            if (n.includes('elevenlabs')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#18181b"/><rect x="13" y="9" width="3.5" height="18" rx="1.5" fill="#fff"/><rect x="19.5" y="9" width="3.5" height="18" rx="1.5" fill="#fff"/></svg>`;
            }
            // Cursor AI
            if (n.includes('cursor')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#09090b"/><polygon points="18,7 28,13 28,23 18,29 8,23 8,13" fill="none" stroke="#fff" stroke-width="2"/><polygon points="18,7 28,13 18,18 8,13" fill="#38bdf8"/><polygon points="18,18 28,13 28,23 18,29" fill="#818cf8" opacity="0.8"/></svg>`;
            }
            // v0 / Vercel
            if (n.includes('v0') || n.includes('vercel')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#000"/><polygon points="18,9 28,26 8,26" fill="#fff"/></svg>`;
            }
            // Bolt.new / Lovable / Replit
            if (n.includes('bolt') || n.includes('lovable') || n.includes('replit')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#ea580c"/><path d="M19.5 7L10 19.5h7.5L16 29l10-12.5h-7.5L19.5 7Z" fill="#fff"/></svg>`;
            }
            // Perplexity AI
            if (n.includes('perplexity')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#0e7490"/><g stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"><path d="M18 7v22M10 11l8 7 8-7M10 25l8-7 8 7"/><rect x="11" y="13" width="14" height="10"/></g></svg>`;
            }
            // Canva
            if (n.includes('canva')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><defs><linearGradient id="canvaG" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#00c4cc"/><stop offset="100%" stop-color="#7d2ae8"/></linearGradient></defs><rect width="36" height="36" rx="10" fill="url(#canvaG)"/><path d="M23.5 13.5a6.5 6.5 0 1 0 0 9" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/></svg>`;
            }
            // Figma
            if (n.includes('figma')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#1e1e1e"/><circle cx="21" cy="18" r="3.5" fill="#1abcfe"/><path d="M14 11h3.5v7H14a3.5 3.5 0 0 1 0-7Z" fill="#f24e1e"/><path d="M17.5 11H21a3.5 3.5 0 0 1 0 7h-3.5v-7Z" fill="#ff7262"/><path d="M14 18h3.5v7H14a3.5 3.5 0 0 1 0-7Z" fill="#a259ff"/><path d="M14 25h3.5v3.5A3.5 3.5 0 0 1 14 25Z" fill="#0acf83"/></svg>`;
            }
            // Gamma / Notion / Zapier / n8n
            if (n.includes('gamma') || n.includes('notion') || n.includes('zapier') || n.includes('n8n')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#ec4899"/><circle cx="12" cy="18" r="3" fill="#fff"/><circle cx="24" cy="12" r="3" fill="#fff"/><circle cx="24" cy="24" r="3" fill="#fff"/><path d="M14.5 17l7-4M14.5 19l7 4" stroke="#fff" stroke-width="2.2"/></svg>`;
            }
            // Adobe Firefly / Express / Podcast
            if (n.includes('adobe') || n.includes('firefly')) {
                return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="#dc2626"/><path d="M18 9L9 27h4.2l2-4.2h5.6l2 4.2H27L18 9Zm0 7.2 1.8 4h-3.6l1.8-4Z" fill="#fff"/></svg>`;
            }
            const initials = name.replace(/[^A-Za-z0-9]/g, '').slice(0, 2).toUpperCase() || 'AI';
            const colors = ['#0284c7', '#7c3aed', '#059669', '#db2777', '#d97706', '#4f46e5'];
            const color = colors[name.length % colors.length];
            return `<svg viewBox="0 0 36 36" class="w-9 h-9"><rect width="36" height="36" rx="10" fill="${color}"/><text x="18" y="22" text-anchor="middle" fill="#fff" font-size="13" font-weight="800" font-family="Inter, sans-serif">${initials}</text></svg>`;
        }

        function getCategoryBadgeGradient(type) {
            const map = {
                text: 'from-cyan-500/20 via-blue-600/10 to-transparent',
                image: 'from-fuchsia-500/20 via-purple-600/10 to-transparent',
                video: 'from-amber-500/20 via-orange-600/10 to-transparent',
                audio: 'from-emerald-500/20 via-teal-600/10 to-transparent',
                code: 'from-indigo-500/20 via-sky-600/10 to-transparent',
                research: 'from-sky-500/20 via-cyan-600/10 to-transparent',
                design: 'from-rose-500/20 via-pink-600/10 to-transparent',
                auto: 'from-violet-500/20 via-purple-600/10 to-transparent'
            };
            return map[type] || map.text;
        }


        function initNeuralCanvas() {
            const canvas = document.getElementById('neural-canvas');
            const heroSection = document.getElementById('bosh-sahifa');
            if (!canvas) return;
            const ctx = canvas.getContext('2d');
            let w, h, nodes = [];
            const mouse = { x: null, y: null, radius: 170 };

            function resize() {
                w = canvas.width = canvas.offsetWidth || window.innerWidth;
                h = canvas.height = canvas.offsetHeight || 650;
                const nodeCount = Math.min(95, Math.max(65, Math.floor((w * h) / 11000)));
                nodes = Array.from({ length: nodeCount }, () => ({
                    x: Math.random() * w,
                    y: Math.random() * h,
                    vx: (Math.random() - 0.5) * 0.85,
                    vy: (Math.random() - 0.5) * 0.85,
                    r: 1.6 + Math.random() * 1.6,
                    color: Math.random() > 0.35 ? '#38bdf8' : '#a855f7'
                }));
            }
            resize();
            window.addEventListener('resize', resize);

            if (heroSection) {
                heroSection.addEventListener('mousemove', (e) => {
                    const rect = canvas.getBoundingClientRect();
                    mouse.x = e.clientX - rect.left;
                    mouse.y = e.clientY - rect.top;
                });
                heroSection.addEventListener('mouseleave', () => {
                    mouse.x = null;
                    mouse.y = null;
                });
            }

            function draw() {
                ctx.clearRect(0, 0, w, h);
                for (let i = 0; i < nodes.length; i++) {
                    const a = nodes[i];
                    a.x += a.vx;
                    a.y += a.vy;

                    if (mouse.x !== null && mouse.y !== null) {
                        const dx = mouse.x - a.x;
                        const dy = mouse.y - a.y;
                        const distM = Math.hypot(dx, dy);
                        if (distM < mouse.radius && distM > 1) {
                            const force = (mouse.radius - distM) / mouse.radius;
                            a.x -= (dx / distM) * force * 1.8;
                            a.y -= (dy / distM) * force * 1.8;

                            ctx.beginPath();
                            ctx.moveTo(a.x, a.y);
                            ctx.lineTo(mouse.x, mouse.y);
                            ctx.strokeStyle = `rgba(168, 85, 247, ${force * 0.55})`;
                            ctx.lineWidth = 1;
                            ctx.stroke();
                        }
                    }

                    if (a.x < 0 || a.x > w) a.vx *= -1;
                    if (a.y < 0 || a.y > h) a.vy *= -1;

                    ctx.beginPath();
                    ctx.arc(a.x, a.y, a.r, 0, Math.PI * 2);
                    ctx.fillStyle = a.color;
                    ctx.fill();

                    for (let j = i + 1; j < nodes.length; j++) {
                        const b = nodes[j];
                        const dist = Math.hypot(a.x - b.x, a.y - b.y);
                        if (dist < 145) {
                            ctx.beginPath();
                            ctx.moveTo(a.x, a.y);
                            ctx.lineTo(b.x, b.y);
                            ctx.strokeStyle = `rgba(56, 189, 248, ${(1 - dist / 145) * 0.65})`;
                            ctx.lineWidth = 0.75;
                            ctx.stroke();
                        }
                    }
                }
                requestAnimationFrame(draw);
            }
            draw();
        }

