        // Step state for two-stage response
        let stepData = null; // { steps: [{mood, text}, {mood, text}], index: 0 }
        // Theme state
        function applyTheme(theme) {
            const root = document.documentElement;
            if (theme === 'dark') root.classList.add('dark'); else root.classList.remove('dark');
            localStorage.setItem('theme', theme);
        }
        function toggleTheme() {
            const isDark = document.documentElement.classList.contains('dark');
            applyTheme(isDark ? 'light' : 'dark');
        }

        // Matrix rain animation
        let matrixCtx = null;
        let matrixCanvas = null;
        let matrixColumns = 0;
        let matrixDrops = [];
        let matrixFontSize = 16;
        let matrixInterval = 60; // ms per step (increase to slow down)
        let matrixLastTs = 0;
        const matrixChars = '01ABCDEFGHIJKLMNOPQRSTUVWXYZあいうえおｱｲｳｴｵ+-*/<>#$%&';

        function setupMatrix() {
            matrixCanvas = document.getElementById('matrix-canvas');
            if (!matrixCanvas) return;
            matrixCtx = matrixCanvas.getContext('2d');
            resizeMatrix();
            requestAnimationFrame(drawMatrix);
        }

        function resizeMatrix() {
            if (!matrixCanvas || !matrixCtx) return;
            matrixCanvas.width = window.innerWidth;
            matrixCanvas.height = window.innerHeight;
            matrixFontSize = Math.max(12, Math.floor(window.innerWidth / 90));
            matrixCtx.font = `${matrixFontSize}px monospace`;
            matrixColumns = Math.floor(matrixCanvas.width / matrixFontSize);
            matrixDrops = Array(matrixColumns).fill(0).map(() => Math.floor(Math.random() * matrixCanvas.height / matrixFontSize));
        }

        function drawMatrix(ts) {
            if (!ts) ts = performance.now();
            if (matrixLastTs === 0) matrixLastTs = ts;
            const delta = ts - matrixLastTs;
            if (delta < matrixInterval) {
                requestAnimationFrame(drawMatrix);
                return;
            }
            matrixLastTs = ts;
            if (!matrixCtx || !matrixCanvas) return;
            // Faint background for trail
            matrixCtx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#000000';
            matrixCtx.globalAlpha = 0.12;
            matrixCtx.fillRect(0, 0, matrixCanvas.width, matrixCanvas.height);
            matrixCtx.globalAlpha = 1;

            const color = getComputedStyle(document.documentElement).getPropertyValue('--matrix-color').trim() || '#00ff88';
            matrixCtx.fillStyle = color;

            for (let i = 0; i < matrixColumns; i++) {
                const text = matrixChars.charAt(Math.floor(Math.random() * matrixChars.length));
                const x = i * matrixFontSize;
                const y = matrixDrops[i] * matrixFontSize;
                matrixCtx.fillText(text, x, y);
                if (y > matrixCanvas.height && Math.random() > 0.99) {
                    matrixDrops[i] = 0;
                }
                matrixDrops[i]++;
            }
            requestAnimationFrame(drawMatrix);
        }

        function extractFirstEmoji(text) {
            try {
                const regex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
                const m = text.match(regex);
                return m ? m[0] : null;
            } catch (e) {
                return null;
            }
        }

        function setFaceFromText(text) {
            const emoji = extractFirstEmoji(text) || '🙂';
            const node = document.getElementById('face-emoji');
            if (node) {
                node.classList.add('anim');
                setTimeout(() => {
                    node.textContent = emoji;
                    node.classList.remove('anim');
                    fitFaceEmoji();
                }, 150);
            }
        }

        function fitFaceEmoji() {
            const container = document.querySelector('.face-container');
            const node = document.getElementById('face-emoji');
            if (!container || !node) return;
            const maxW = container.clientWidth - 16;
            const maxH = container.clientHeight - 16;
            let size = 96;
            node.style.fontSize = size + 'px';
            node.style.whiteSpace = 'nowrap';
            for (let i = 0; i < 12; i++) {
                const w = node.scrollWidth;
                const h = node.scrollHeight;
                if (w <= maxW && h <= maxH) break;
                size = Math.max(24, Math.floor(size * 0.9));
                node.style.fontSize = size + 'px';
            }
        }

        function extractJsonObject(text) {
            if (!text) return null;
            text = text.replace(/```json|```/g, '').trim();
            const start = text.indexOf('{');
            if (start === -1) return null;
            let depth = 0, inStr = false, esc = false, end = -1;
            for (let i = start; i < text.length; i++) {
                const ch = text[i];
                if (inStr) {
                    if (esc) { esc = false; }
                    else if (ch === '\\') { esc = true; }
                    else if (ch === '"') { inStr = false; }
                } else {
                    if (ch === '"') inStr = true;
                    else if (ch === '{') depth++;
                    else if (ch === '}') {
                        depth--;
                        if (depth === 0) { end = i; break; }
                    }
                }
            }
            if (end === -1) return null;
            const candidate = text.substring(start, end + 1);
            try { return JSON.parse(candidate); } catch (_) { return null; }
        }

        function disableInput(disabled) {
            const input = document.getElementById('user-input');
            const btn = document.getElementById('send-btn');
            if (input) input.disabled = disabled;
            if (btn) btn.disabled = disabled;
        }

        function showNextStep() {
            if (!stepData) return;
            if (stepData.index >= stepData.steps.length - 1) return;
            stepData.index += 1;
            const s = stepData.steps[stepData.index];
            if (window.__lastResponseSecondEmoji) {
                const node = document.getElementById('face-emoji');
                if (node) {
                    node.classList.add('anim');
                    setTimeout(() => { node.textContent = window.__lastResponseSecondEmoji; node.classList.remove('anim'); fitFaceEmoji(); }, 150);
                }
            } else {
                setFaceFromText(s.text);
            }
            addMessage(s.text, false);
            if (stepData.index >= stepData.steps.length - 1) {
                document.getElementById('next-btn').disabled = true;
                disableInput(false);
            }
        }

        async function sendMessage() {
            const input = document.getElementById('user-input');
            const message = input.value.trim();
            if (!message) return;

            addMessage(message, true);
            input.value = '';
            addLoadingMessage();
            setFaceFromText('🤔');
            disableInput(true);

            try {
                const resp = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                const data = await resp.json();
                removeLoadingMessage();

                if (data.error) {
                    addMessage('Hata: ' + data.error, false);
                    disableInput(false);
                    return;
                }

                // ANIMAL RESPONSE BRANCH
                if (data && data.animal) {
                    if (data.animal_emoji) {
                        const node = document.getElementById('face-emoji');
                        if (node) {
                            node.classList.add('anim');
                            setTimeout(() => { node.textContent = data.animal_emoji; node.classList.remove('anim'); fitFaceEmoji(); }, 150);
                        }
                    }
                    if (data.type === 'image' && data.image_url) {
                        addMessage(data.response || 'Görsel hazır.', false);
                        const chatBox = document.getElementById('chat-box');
                        const imgWrap = document.createElement('div');
                        imgWrap.className = 'message bot';
                        const img = document.createElement('img');
                        img.src = data.image_url;
                        img.alt = data.animal + ' image';
                        img.style.maxWidth = '100%';
                        img.style.borderRadius = '6px';
                        img.style.cursor = 'zoom-in';
                        img.addEventListener('click', () => openLightbox(data.image_url));
                        imgWrap.appendChild(img);
                        chatBox.appendChild(imgWrap);
                        chatBox.scrollTop = chatBox.scrollHeight;
                        setActiveFunctionGlow(data.animal, data.type);
                        disableInput(false);
                        return;
                    } else {
                        addMessage(data.response || 'Tamam.', false);
                        setActiveFunctionGlow(data.animal, data.type);
                        disableInput(false);
                        return;
                    }
                }

                // Debug bölümleri kaldırıldı

                // RAG (PDF) response branch
                if (data && (data.rag_source || data.rag_emoji)) {
                    // RAG için özel davranış: PDF emojisi + tek seferde 5 cümle
                    handleRagResponse(data);
                    setActivePdfGlow(data.rag_source, data.rag_emoji);
                    disableInput(false);
                    return;
                }

                // Try parse JSON (ilk/ikinci ruh hali-cevap), fallback to plain text
                let steps = null;
                const j = extractJsonObject(data.response);
                if (j && j.ilk_ruh_hali && j.ilk_cevap && j.ikinci_ruh_hali && j.ikinci_cevap) {
                    steps = [
                        { mood: j.ilk_ruh_hali, text: j.ilk_cevap },
                        { mood: j.ikinci_ruh_hali, text: j.ikinci_cevap }
                    ];
                }

                if (steps) {
                    // Non-animal branch: highlight container edges
                    try {
                        const cont = document.querySelector('.container');
                        cont && cont.classList.add('glow-green');
                        setTimeout(() => cont && cont.classList.remove('glow-green'), 700);
                    } catch (_) {}
                    stepData = { steps, index: 0 };
                    // Show first (server-provided emoji preferred)
                    addMessage(steps[0].text, false);
                    if (data.first_emoji) {
                        const node = document.getElementById('face-emoji');
                        if (node) {
                            node.classList.add('anim');
                            setTimeout(() => { node.textContent = data.first_emoji; node.classList.remove('anim'); fitFaceEmoji(); }, 150);
                        }
                    } else {
                        setFaceFromText(steps[0].text);
                    }
                    const nextBtn = document.getElementById('next-btn');
                    nextBtn.disabled = false;
                    // second emoji cache for next step
                    window.__lastResponseSecondEmoji = data.second_emoji || null;
                } else {
                    // Plain text behavior
                    addMessage(data.response, false);
                    if (data.first_emoji) {
                        // Duygu sistemi: container'ı yeşil yap
                        try {
                            const cont = document.querySelector('.container');
                            cont && cont.classList.add('glow-green');
                            setTimeout(() => cont && cont.classList.remove('glow-green'), 700);
                        } catch (_) {}
                        
                        const node = document.getElementById('face-emoji');
                        if (node) {
                            node.classList.add('anim');
                            setTimeout(() => { node.textContent = data.first_emoji; node.classList.remove('anim'); fitFaceEmoji(); }, 150);
                        }
                    } else {
                        setFaceFromText(data.response);
                    }
                    disableInput(false);
                }

                if (data.stats) {
                    document.getElementById('req-count').textContent = data.stats.requests;
                }
            } catch (e) {
                removeLoadingMessage();
                addMessage('Bağlantı hatası: ' + e.message, false);
                setFaceFromText('😵');
                disableInput(false);
            }
        }

        function addMessage(content, isUser) {
            const chatBox = document.getElementById('chat-box');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + (isUser ? 'user' : 'bot');
            messageDiv.innerHTML = '<pre>' + content + '</pre>';
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function addLoadingMessage() {
            const chatBox = document.getElementById('chat-box');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot loading';
            messageDiv.id = 'loading-message';
            messageDiv.textContent = 'Model düşünüyor...';
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function removeLoadingMessage() {
            const loadingMsg = document.getElementById('loading-message');
            if (loadingMsg) loadingMsg.remove();
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter') sendMessage();
        }
        window.addEventListener('resize', fitFaceEmoji);
        window.addEventListener('resize', resizeMatrix);
        window.addEventListener('load', () => {
            const saved = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
            applyTheme(saved);
            fitFaceEmoji();
            setupMatrix();
        });
        // Lightbox logic
        function openLightbox(url) {
            const lb = document.getElementById('lightbox');
            const lbImg = document.getElementById('lightbox-img');
            const dl = document.getElementById('lightbox-download');
            if (!lb || !lbImg || !dl) return;
            lbImg.src = url;
            dl.href = url;
            const filename = url.split('/').pop() || 'image.jpg';
            dl.setAttribute('download', filename);
            lb.classList.add('open');
        }
        function closeLightbox() {
            const lb = document.getElementById('lightbox');
            if (lb) lb.classList.remove('open');
        }
        document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeLightbox(); });
        // Wires + draggable nodes logic
        function setActiveFunctionGlow(animal, type) {
            clearGlow();
            if (!animal) return;
            const id = `${animal}_${type === 'image' ? 'photo' : 'facts'}`;
            const node = document.getElementById('fn-' + id);
            const wire = document.getElementById('wire-' + id);
            if (node) node.classList.add('active');
            if (wire) wire.classList.add('glow');
        }
        function clearGlow() {
            document.querySelectorAll('.func-node.active').forEach(n => n.classList.remove('active'));
            document.querySelectorAll('.wire.glow').forEach(n => n.classList.remove('glow'));
        }
        function setActivePdfGlow(pdfId, emoji) {
            clearGlow();
            if (!pdfId) return;
            const node = document.getElementById('fn-' + pdfId);
            const wire = document.getElementById('wire-' + pdfId);
            if (node) node.classList.add('active');
            if (wire) wire.classList.add('glow');
            if (emoji) {
                const face = document.getElementById('face-emoji');
                if (face) {
                    face.classList.add('anim');
                    setTimeout(() => { face.textContent = emoji; face.classList.remove('anim'); fitFaceEmoji(); }, 150);
                }
            }
        }

        function handleRagResponse(data) {
            // RAG için özel davranış: tek seferde 5 cümle, sonraki tuşu yok
            const response = data.response || 'Tamam.';
            
            // Cümleleri ayır (nokta, ünlem, soru işareti ile)
            const sentences = response.split(/[.!?]+/).filter(s => s.trim().length > 0);
            
            // Maksimum 5 cümle al
            const limitedSentences = sentences.slice(0, 5);
            const finalResponse = limitedSentences.join('. ') + (limitedSentences.length < sentences.length ? '...' : '');
            
            // Tek seferde tüm mesajı ekle (sonraki tuşu yok)
            addMessage(finalResponse, false);
        }
        function quickPrompt(text) {
            const input = document.getElementById('user-input');
            if (!input || input.disabled) return;
            input.value = text;
            input.focus();
        }

        const DRAGGABLES = [
            { id: 'fn-dog_photo', side: 'left', prompt: 'Bana bir köpek fotoğrafı ver', top: 140, left: 16 },
            { id: 'fn-dog_facts', side: 'left', prompt: 'Bana bir köpek bilgisi ver', top: 200, left: 16 },
            { id: 'fn-cat_photo', side: 'left', prompt: 'Bana bir kedi fotoğrafı ver', top: 260, left: 16 },
            { id: 'fn-cat_facts', side: 'right', prompt: 'Bana bir kedi bilgisi ver', top: 140, right: 16 },
            { id: 'fn-fox_photo', side: 'right', prompt: 'Bana bir tilki fotoğrafı ver', top: 200, right: 16 },
            { id: 'fn-duck_photo', side: 'right', prompt: 'Bana bir ördek fotoğrafı ver', top: 260, right: 16 },
            // RAG PDF nodes
            { id: 'fn-pdf-python', side: 'left', prompt: 'Python PDF bağlamıyla: Python nedir?', top: 320, left: 16 },
            { id: 'fn-pdf-anayasa', side: 'right', prompt: 'Anayasa PDF bağlamıyla: Temel haklar nedir?', top: 320, right: 16 },
            { id: 'fn-pdf-clean', side: 'right', prompt: 'Clean Architecture PDF bağlamıyla: Entities nedir?', top: 380, right: 16 },
        ];

        // Rope with many segments (full rope)
        const ROPES = {}; // key → { points:[{x,y,vx,vy}], pathEl, side, restLen }
        const SEGMENTS = 12; // daha pürüzsüz halat
        const DAMPING = 0.965; // daha yüksek sürtünme, ani fırlamayı azalt
        const CONSTRAINT_ITERS = 3;

        function initDraggables() {
            DRAGGABLES.forEach(cfg => {
                const el = document.getElementById(cfg.id);
                if (!el) return;
                if (cfg.left !== undefined) el.style.left = cfg.left + 'px';
                if (cfg.right !== undefined) el.style.right = cfg.right + 'px';
                el.style.top = cfg.top + 'px';
                el.dataset.side = cfg.side;
                el.addEventListener('click', () => quickPrompt(cfg.prompt));
                makeDraggable(el);
            });
            initRopes();
            updateRopesImmediate();
            requestAnimationFrame(stepRopes);
        }

        function makeDraggable(node) {
            let dragging = false; let startX = 0; let startY = 0; let startLeft = 0; let startTop = 0; let lastVX = 0; let lastVY = 0; let lastTs = 0; let prevLeft = 0; let prevTop = 0;
            node.addEventListener('pointerdown', (e) => {
                dragging = true; node.setPointerCapture(e.pointerId);
                startX = e.clientX; startY = e.clientY; lastVX = 0; lastVY = 0; lastTs = performance.now();
                const rect = node.getBoundingClientRect();
                startLeft = rect.left; startTop = rect.top; prevLeft = rect.left; prevTop = rect.top;
            });
            node.addEventListener('pointermove', (e) => {
                if (!dragging) return;
                const now = performance.now();
                const dt = Math.max(0.016, (now - lastTs) / 1000);
                const dx = e.clientX - startX; const dy = e.clientY - startY;
                let newLeft = Math.max(8, Math.min(window.innerWidth - node.offsetWidth - 8, startLeft + dx));
                const newTop = Math.max(80, Math.min(window.innerHeight - node.offsetHeight - 8, startTop + dy));
                // Side constraint: keep node on its side of the container
                try {
                    const cRect = document.querySelector('.container').getBoundingClientRect();
                    const gap = 12;
                    if (node.dataset.side === 'left') {
                        const maxLeft = cRect.left - node.offsetWidth - gap;
                        newLeft = Math.min(newLeft, maxLeft);
                    } else if (node.dataset.side === 'right') {
                        const minLeft = cRect.right + gap;
                        newLeft = Math.max(newLeft, minLeft);
                    }
                } catch (_) { /* ignore */ }
                node.style.left = newLeft + 'px'; node.style.right = 'auto';
                node.style.top = newTop + 'px';
                // Hızı bir önceki konuma göre hesapla (daha stabil)
                lastVX = (newLeft - prevLeft) / dt;
                lastVY = (newTop - prevTop) / dt;
                prevLeft = newLeft; prevTop = newTop; lastTs = now;
                updateRopesImmediate();
            });
            node.addEventListener('pointerup', () => { dragging = false; impartVelocity(node, lastVX, lastVY); lastVX = 0; lastVY = 0; });
            node.addEventListener('pointercancel', () => { dragging = false; });
        }

        function initRopes() {
            const svg = document.getElementById('wires');
            const container = document.querySelector('.container');
            if (!svg || !container) return;
            svg.setAttribute('width', window.innerWidth);
            svg.setAttribute('height', window.innerHeight);
            DRAGGABLES.forEach(cfg => {
                const key = cfg.id.replace('fn-','');
                let path = document.getElementById('wire-' + key);
                if (!path) {
                    path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                    path.setAttribute('id', 'wire-' + key);
                    path.setAttribute('class', 'wire');
                    svg.appendChild(path);
                }
                // Her halat için sabit ankraj yüksekliği oranı (container yüksekliğine göre)
                const nRect = document.getElementById(cfg.id).getBoundingClientRect();
                const cRect = container.getBoundingClientRect();
                const ratio = Math.min(0.95, Math.max(0.05, (nRect.top + nRect.height / 2 - cRect.top) / Math.max(1, cRect.height)));
                cfg.anchorRatio = ratio;
                ROPES[key] = { points: [], pathEl: path, side: cfg.side, restLen: 0 };
            });
        }

        function ropeEndpoints(key) {
            const container = document.querySelector('.container');
            const node = document.getElementById('fn-' + key);
            const cRect = container.getBoundingClientRect();
            const nRect = node.getBoundingClientRect();
            const cfg = DRAGGABLES.find(c => c.id === 'fn-' + key) || { side: 'left', anchorRatio: 0.5 };
            const anchorY = Math.min(Math.max(cRect.top + (cfg.anchorRatio || 0.5) * cRect.height, cRect.top + 24), cRect.bottom - 24);
            return {
                startX: nRect.left + nRect.width / 2,
                startY: nRect.top + nRect.height / 2,
                endX: (cfg.side === 'left') ? cRect.left : cRect.right,
                endY: anchorY
            };
        }

        function ensurePoints(key) {
            const rope = ROPES[key];
            if (!rope) return;
            const ep = ropeEndpoints(key);
            if (rope.points.length === 0) {
                rope.points = [];
                for (let i = 0; i <= SEGMENTS; i++) {
                    const t = i / SEGMENTS;
                    rope.points.push({ x: ep.startX + (ep.endX - ep.startX) * t, y: ep.startY + (ep.endY - ep.startY) * t, vx: 0, vy: 0 });
                }
                const totalDist = Math.hypot(ep.endX - ep.startX, ep.endY - ep.startY);
                rope.restLen = (totalDist / SEGMENTS) * 1.02; // biraz gevşek
            } else {
                // Uçları güncelle (düğüm ve anchor sabit nokta)
                rope.points[0].x = ep.startX; rope.points[0].y = ep.startY;
                rope.points[SEGMENTS].x = ep.endX; rope.points[SEGMENTS].y = ep.endY;
            }
        }

        function stepRopes(ts) {
            const container = document.querySelector('.container');
            if (!container) return;
            for (const key in ROPES) {
                const rope = ROPES[key];
                ensurePoints(key);
                const pts = rope.points;
                // Hedef segment uzunluğu: uçlar arası mesafeye göre (kısalma serbest, uzama değil)
                const ep = ropeEndpoints(key);
                const targetLen = (Math.hypot(ep.endX - ep.startX, ep.endY - ep.startY) / SEGMENTS) * 1.02;
                if (!rope.restLen || rope.restLen > targetLen) rope.restLen = targetLen;
                // Tüm orta noktalara sürtünme uygula
                for (let i = 1; i < pts.length - 1; i++) { const p = pts[i]; p.vx *= DAMPING; p.vy *= DAMPING; p.x += p.vx; p.y += p.vy; }
                // Uzunluk kısıtları (Verlet benzeri düzeltme)
                for (let k = 0; k < CONSTRAINT_ITERS; k++) {
                    for (let i = 0; i < pts.length - 1; i++) {
                        const a = pts[i]; const b = pts[i + 1];
                        let dx = b.x - a.x; let dy = b.y - a.y; let dist = Math.hypot(dx, dy) || 0.0001;
                        const diff = (dist - rope.restLen) / dist;
                        if (i === 0) { b.x -= dx * diff; b.y -= dy * diff; }
                        else if (i + 1 === SEGMENTS) { a.x += dx * diff; a.y += dy * diff; }
                        else { a.x += dx * diff * 0.5; a.y += dy * diff * 0.5; b.x -= dx * diff * 0.5; b.y -= dy * diff * 0.5; }
                    }
                }
                // Anchor (container tarafı) sabit: p[SEGMENTS] container kenarının tam üstünde kalsın
                const cRect = document.querySelector('.container').getBoundingClientRect();
                const anchor = pts[SEGMENTS];
                const cfg = DRAGGABLES.find(c => c.id === 'fn-' + key) || { side: 'left', anchorRatio: 0.5 };
                if (cfg.side === 'left') { anchor.x = cRect.left; } else { anchor.x = cRect.right; }
                anchor.y = Math.min(Math.max(cRect.top + (cfg.anchorRatio || 0.5) * cRect.height, cRect.top + 24), cRect.bottom - 24);
                drawRope(key);
            }
            requestAnimationFrame(stepRopes);
        }

        function drawRope(key) {
            const rope = ROPES[key]; if (!rope) return;
            const pts = rope.points;
            if (!pts || pts.length < 2) return;
            // Çok parçalı yumuşak yol
            let d = `M ${pts[0].x},${pts[0].y}`;
            for (let i = 1; i < pts.length; i++) {
                const p0 = pts[i - 1]; const p1 = pts[i];
                const cx = (p0.x + p1.x) / 2; const cy = (p0.y + p1.y) / 2;
                d += ` Q ${cx},${cy} ${p1.x},${p1.y}`;
            }
            rope.pathEl.setAttribute('d', d);
        }

        function updateRopesImmediate() {
            for (const key in ROPES) { ensurePoints(key); drawRope(key); }
        }

        function impartVelocity(node, vx, vy) {
            // Sürükleme bırakıldığında yumuşak momentum ver (clamp)
            const key = (node.id || '').replace('fn-','');
            const rope = ROPES[key]; if (!rope) return;
            if (!isFinite(vx) || !isFinite(vy)) { vx = 0; vy = 0; }
            let speed = Math.hypot(vx, vy);
            if (speed > 800) { const s = 800 / Math.max(1e-6, speed); vx *= s; vy *= s; }
            const n = rope.points.length;
            for (let i = 1; i < n - 1; i++) {
                const falloff = 1 - (i / (n - 1)); // uca yakın daha fazla pay
                rope.points[i].vx += vx * 0.01 * falloff;
                rope.points[i].vy += vy * 0.01 * falloff;
            }
            // Her çekmede halat biraz kısalsın (minimum sınır ile)
            const ep = ropeEndpoints(key);
            const minLen = Math.max(8, Math.hypot(ep.endX - ep.startX, ep.endY - ep.startY) / SEGMENTS * 0.6);
            rope.restLen = Math.max(minLen, (rope.restLen || minLen) * 0.98);
        }

        function recomputeRestLenAll() {
            for (const key in ROPES) {
                const rope = ROPES[key];
                const ep = ropeEndpoints(key);
                const target = (Math.hypot(ep.endX - ep.startX, ep.endY - ep.startY) / SEGMENTS) * 1.02;
                rope.restLen = Math.min(rope.restLen || target, target);
            }
        }

        window.addEventListener('resize', () => { const svg = document.getElementById('wires'); if (svg) { svg.setAttribute('width', window.innerWidth); svg.setAttribute('height', window.innerHeight); } recomputeRestLenAll(); updateRopesImmediate(); });
        window.addEventListener('scroll', updateRopesImmediate, { passive: true });
        window.addEventListener('load', initDraggables);