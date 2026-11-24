'use strict';
(() => {
    const D = window.AIOlamiData;
    const $ = id => document.getElementById(id);
    const el = (tag, className = '', text = '') => {
        const node = document.createElement(tag);
        node.className = className;
        if (text !== '') node.textContent = text;
        return node;
    };
    const link = (label, url, className = '') => {
        const node = el('a', className, label);
        node.href = D.httpsURL(url); node.target = '_blank'; node.rel = 'noopener noreferrer';
        return node;
    };
    const logo = name => {
        const node = el('span', 'shrink-0');
        // The SVG helper returns only fixed markup and alphanumeric initials.
        node.innerHTML = getBrandLogoSVG(name);
        node.setAttribute('aria-hidden', 'true');
        return node;
    };
    const categoryTypes = ['text', 'image', 'video', 'audio', 'code', 'research', 'design', 'auto'];
    // Editorial introductions carried over from the original catalogue. No pricing,
    // usage numbers, model versions, or popularity rankings are asserted here.
    const curated = [
        ['chatgpt', 'ChatGPT', 'OpenAI', 0, 'Matn yozish, suhbat va ma’lumotlarni tahlil qilish uchun AI yordamchisi.', 'https://chatgpt.com/'],
        ['gemini', 'Google Gemini', 'Google', 0, 'Matn va boshqa turdagi ma’lumotlar bilan ishlashga mo‘ljallangan AI yordamchisi.', 'https://gemini.google.com/'],
        ['deepseek', 'DeepSeek', 'DeepSeek', 0, 'Suhbat, mantiqiy masalalar va dasturlash vazifalari uchun AI xizmati.', 'https://www.deepseek.com/'],
        ['claude', 'Claude', 'Anthropic', 4, 'Matn, hujjatlar va dasturiy kod bilan ishlash uchun AI yordamchisi.', 'https://claude.ai/'],
        ['midjourney', 'Midjourney', 'Midjourney', 1, 'Matnli tavsiflar asosida tasvir yaratish vositasi.', 'https://www.midjourney.com/'],
        ['sora', 'Sora', 'OpenAI', 2, 'Generativ video yaratishga mo‘ljallangan AI vositasi.', 'https://openai.com/sora/'],
        ['runway', 'Runway', 'Runway', 2, 'Video yaratish va tahrirlash uchun AI vositalari.', 'https://runwayml.com/'],
        ['suno', 'Suno', 'Suno', 3, 'Musiqa va qo‘shiq yaratish uchun generativ AI xizmati.', 'https://suno.com/'],
        ['elevenlabs', 'ElevenLabs', 'ElevenLabs', 3, 'Sun’iy ovoz yaratish va audio bilan ishlash vositalari.', 'https://elevenlabs.io/'],
        ['cursor', 'Cursor', 'Anysphere', 4, 'Dasturiy kod bilan ishlash uchun AI imkoniyatlari bor muharrir.', 'https://cursor.com/'],
        ['perplexity', 'Perplexity', 'Perplexity', 5, 'Savollar bo‘yicha manbali qidiruv va tadqiqotga yordam beruvchi AI xizmati.', 'https://www.perplexity.ai/'],
        ['canva', 'Canva AI', 'Canva', 6, 'Dizayn yaratishda yordam beruvchi AI funksiyalariga ega platforma.', 'https://www.canva.com/ai/']
    ].map(([id, name, developer, categoryIndex, description, url]) => ({id, name, developer,
        category: D.categories[categoryIndex], description, url, official_url: url,
        source_url: url, source: 'Tahririy tavsif', editorial: true, status: 'approved'}));
    let aiList = curated.slice(), promoData = {promotions: []};
    let currentCategory = 'Hammasi', currentPricing = 'all', currentSearch = '', visibleLimit = 24;
    let selectedReviewStars = 5, selectedPromoType = 'all', currentStats = 'total', previousFocus = null;
    const pricingLabel = ai => ai.pricing_model?.length ? 'Manbada: ' + ai.pricing_model.join(', ') : ai.free_plan === true ? 'Manbada bepul tarif qayd etilgan' : 'Tarif tekshirilmagan';
    const priceButtons = [...document.querySelectorAll('.price-btn')];
    // Unknown price is explicit; missing data never implies a paid or free plan.
    const priceNote = el('span', 'text-sm text-slate-400', 'Tarif filtrlari manba ma’lumotiga asoslanadi; joriy shartlarni xizmat saytida tekshiring.');
    priceButtons[priceButtons.length - 1]?.after(priceNote);
    const unknownButton = el('button', 'price-btn px-3 py-1 rounded-lg text-xs font-semibold bg-white/5 text-slate-300', 'Tekshirilmagan');
    unknownButton.type = 'button'; unknownButton.dataset.price = 'unknown';
    priceNote.before(unknownButton); priceButtons.push(unknownButton);

    function getFilteredAIs() {
        const query = currentSearch.trim().toLowerCase();
        return aiList.filter(ai => (currentCategory === 'Hammasi' || ai.category === currentCategory)
            && (currentPricing === 'all' || D.pricingFlags(ai)[currentPricing] === true)
            && (!query || [ai.name, ai.description, ai.category, ai.developer || '', ai.source].join(' ').toLowerCase().includes(query)));
    }
    function renderCards() {
        const list = getFilteredAIs(), grid = $('ai-grid');
        $('ai-count').textContent = list.length.toLocaleString('uz-UZ'); grid.replaceChildren();
        $('empty-state').classList.toggle('hidden', list.length > 0);
        $('empty-state').querySelector('p').textContent = 'Boshqa kalit so‘z yozib ko‘ring yoki filtrlarni tozalang. Tariflar faqat manbada qayd etilgan yozuvlar bo‘yicha filtrlanadi.';
        $('load-more-wrap').classList.toggle('hidden', list.length <= visibleLimit);
        $('load-more-label').textContent = `Yana ${Math.min(40, Math.max(0, list.length - visibleLimit))} ta AI yuklash`;
        list.slice(0, visibleLimit).forEach(ai => {
            const card = el('button', 'glass-card ai-tilt-card rounded-3xl overflow-hidden text-left flex flex-col justify-between group w-full');
            card.type = 'button'; card.addEventListener('click', () => openModalById(ai.id));
            if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                card.addEventListener('pointermove', event => {
                    if (event.pointerType === 'touch') return;
                    const bounds = card.getBoundingClientRect(), x = (event.clientX - bounds.left) / bounds.width, y = (event.clientY - bounds.top) / bounds.height;
                    card.style.setProperty('--mx', x * 100 + '%'); card.style.setProperty('--my', y * 100 + '%');
                    card.style.transform = `perspective(900px) rotateX(${(0.5 - y) * 5}deg) rotateY(${(x - 0.5) * 5}deg)`;
                });
                card.addEventListener('pointerleave', () => { card.style.transform = ''; });
            }
            const type = categoryTypes[D.categories.indexOf(ai.category)];
            const head = el('div', 'w-full p-5 bg-gradient-to-br ' + getCategoryBadgeGradient(type) + ' border-b border-white/5 flex items-center gap-3');
            const title = el('div', 'min-w-0'); title.append(el('h3', 'font-bold text-white text-base truncate group-hover:text-cyan-300', ai.name), el('p', 'text-xs text-slate-400 truncate', ai.editorial ? ai.developer : ai.source));
            head.append(logo(ai.name), title);
            const body = el('div', 'p-5 flex-1');
            body.append(el('span', 'inline-block px-2.5 py-1 mb-3 rounded-full text-xs bg-white/10 text-slate-200', ai.category), el('p', 'text-sm text-slate-300 leading-relaxed line-clamp-3', ai.description));
            const foot = el('div', 'w-full px-5 py-3.5 border-t border-white/5 bg-dark-950/40 flex items-center justify-between gap-2 text-xs');
            foot.append(el('span', 'text-slate-400', ai.editorial ? 'Tahririy tanlov' : 'Manbadan saralangan'), el('span', 'text-cyan-300 font-semibold', 'Batafsil'));
            card.append(head, body, foot); grid.append(card);
        });
        document.querySelectorAll('.cat-btn').forEach(b => { b.className = 'cat-btn px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ' + (b.dataset.cat === currentCategory ? 'bg-cyan-500 text-slate-950' : 'bg-white/5 text-slate-300 hover:bg-white/10'); });
        priceButtons.forEach(b => { b.className = 'price-btn px-3 py-1 rounded-lg text-xs font-semibold transition ' + (b.dataset.price === currentPricing ? 'bg-indigo-500 text-white' : 'bg-white/5 text-slate-300 hover:bg-white/10'); });
        const parts = [];
        if (currentCategory !== 'Hammasi') parts.push(currentCategory);
        if (currentPricing !== 'all') parts.push(priceButtons.find(b => b.dataset.price === currentPricing)?.textContent || currentPricing);
        if (currentSearch) parts.push('Qidiruv: ' + currentSearch);
        $('active-filter-banner').classList.toggle('hidden', !parts.length);
        $('active-filter-text').textContent = parts.join(' • ');
    }
    function renderMetrics() {
        $('metric-total').textContent = aiList.length;
        $('metric-categories').textContent = new Set(aiList.map(a => a.category)).size;
        $('metric-discovered').textContent = aiList.filter(a => !a.editorial).length;
        $('metric-promos').textContent = D.activePromotions(promoData).length;
        renderStatistics();
    }
    function renderStatistics() {
        const container = $('stats-bars'); container.replaceChildren();
        const rows = D.statistics(aiList, currentStats), maximum = Math.max(1, ...rows.map(row => row.value));
        rows.forEach(item => {
            const row = el('div'), heading = el('div', 'flex justify-between gap-3 text-sm mb-2');
            heading.append(el('span', 'text-slate-300', item.title), el('span', 'text-cyan-300 font-bold', currentStats === 'share' ? item.value.toFixed(1) + '%' : item.value.toLocaleString('uz-UZ') + ' ta'));
            const track = el('div', 'h-2 bg-white/5 rounded-full overflow-hidden'), fill = el('div', 'stat-bar-fill h-full rounded-full bg-gradient-to-r from-cyan-500 via-indigo-500 to-fuchsia-500');
            track.append(fill); row.append(heading, track); container.append(row);
            requestAnimationFrame(() => { fill.style.width = item.value / (currentStats === 'share' ? 100 : maximum) * 100 + '%'; });
        });
        $('stats-note').textContent = currentStats === 'free' ? 'Bepul tarif manbada qayd etilgan vositalar. Bu joriy narx yoki cheksiz foydalanish kafolati emas; noma’lum tariflar hisobga kiritilmaydi.'
            : currentStats === 'imported' ? 'Ochiq kataloglardan olingan yozuvlar. Import vaqti mahsulot yaratilgan yoki ishga tushgan sana degani emas.'
            : 'Raqamlar shu katalogdagi takrorsiz yozuvlardan hisoblanadi. Ulushlar katalog tarkibini bildiradi.';
        document.querySelectorAll('[data-stats]').forEach(button => {
            const active = button.dataset.stats === currentStats;
            button.setAttribute('aria-selected', String(active));
            button.className = 'stats-tab-btn px-3.5 py-2 rounded-lg text-sm font-bold transition ' + (active ? 'bg-cyan-500 text-slate-950' : 'text-slate-300 hover:text-white');
        });
    }
    function initBrandMarquee() {
        const container = $('brand-marquee'); container.replaceChildren();
        [...curated, ...curated].forEach(ai => {
            const button = el('button', 'flex items-center gap-2.5 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 shrink-0 transition');
            button.type = 'button'; button.append(logo(ai.name), el('span', 'text-xs font-bold text-white', ai.name));
            button.addEventListener('click', () => openModalById(ai.id)); container.append(button);
        });
    }
    function openModalById(id) {
        const ai = aiList.find(item => item.id === id); if (!ai) return;
        const content = $('modal-content'); content.replaceChildren();
        const head = el('div', 'flex items-center gap-4 mb-5 pr-8'), title = el('div');
        title.append(el('h3', 'text-xl sm:text-2xl font-extrabold text-white', ai.name), el('p', 'text-sm text-cyan-400', ai.category)); head.append(logo(ai.name), title);
        content.append(head, el('p', 'text-sm text-slate-300 leading-relaxed mb-5', ai.description));
        content.append(el('p', 'text-sm text-amber-300 mb-4', pricingLabel(ai) + '. Joriy narx va foydalanish cheklovlarini xizmatning o‘zida aniqlashtiring.'));
        const meta = el('div', 'p-4 rounded-2xl bg-white/5 border border-white/10 mb-5 text-sm text-slate-400');
        meta.append(el('p', '', ai.editorial ? 'Tahririy tavsif. Imkoniyatlar xizmat yangilanishi bilan o‘zgarishi mumkin.' : ai.imported ? 'Ochiq AI katalogidan olingan yozuv; tavsif va yo‘nalish moslashtirilgan. Har bir xizmat alohida jonli tekshirilgan degan da’vo yo‘q.' : 'Avtomatik qoida asosida AI vositasi sifatida saralangan. Manba tavsifini quyida tekshirishingiz mumkin.'));
        if (ai.source_date) meta.append(el('p', 'mt-2', 'Manbadagi sana: ' + ai.source_date));
        if (Number.isFinite(Date.parse(ai.approved_at))) meta.append(el('p', 'mt-2', 'Saralangan: ' + new Date(ai.approved_at).toLocaleString('uz-UZ')));
        meta.append(link('Manba: ' + ai.source, ai.source_url, 'inline-block mt-2 text-cyan-300 underline')); content.append(meta);
        const actions = el('div', 'flex flex-wrap gap-3');
        actions.append(link(ai.official_url ? 'Xizmat saytini ochish' : 'Manbadagi sahifani ochish', ai.official_url || ai.url, 'py-3 px-5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 text-white text-sm font-bold text-center'));
        content.append(actions); previousFocus = document.activeElement;
        $('ai-modal').classList.remove('hidden'); $('ai-modal').classList.add('flex');
        $('ai-modal').setAttribute('role', 'dialog'); $('ai-modal').setAttribute('aria-modal', 'true'); $('ai-modal').setAttribute('aria-label', ai.name);
        document.body.style.overflow = 'hidden'; $('ai-modal').querySelector('button').focus();
    }
    function closeModal() { $('ai-modal').classList.add('hidden'); $('ai-modal').classList.remove('flex'); document.body.style.overflow = ''; previousFocus?.focus(); }
    function renderComparison() {
        const a = aiList.find(x => x.id === $('compare-a').value), b = aiList.find(x => x.id === $('compare-b').value);
        if (!a || !b) return;
        const table = el('table', 'w-full text-left border-collapse text-sm'), body = el('tbody', 'divide-y divide-white/10');
        [['Vosita', a.name, b.name], ['Yo‘nalish', a.category, b.category], ['Manba', a.source, b.source], ['Tarif', pricingLabel(a), pricingLabel(b)], ['Tavsif', a.description, b.description]].forEach((values, index) => {
            const row = el('tr'); values.forEach((value, i) => row.append(el(index === 0 ? 'th' : 'td', 'py-3 px-3 ' + (i ? 'text-slate-200' : 'text-slate-400'), value))); body.append(row);
        }); table.append(body); $('comparison-table').replaceChildren(table);
    }
    function initComparisonSelects() {
        ['compare-a', 'compare-b'].forEach(id => {
            const select = $(id), prior = select.value; select.replaceChildren();
            const query = $('search-' + id).value.trim().toLowerCase();
            const chosen = aiList.find(a => a.id === prior) || (id === 'compare-b' ? aiList[1] : aiList[0]);
            const matches = aiList.filter(ai => !query || ai.name.toLowerCase().includes(query)).slice(0, 200);
            if (chosen && !matches.includes(chosen)) matches.unshift(chosen);
            matches.forEach(ai => { const option = el('option', '', ai.name); option.value = ai.id; select.append(option); });
            select.value = chosen?.id || '';
        }); renderComparison();
    }
    function renderPromotions() {
        const active = D.activePromotions(promoData), items = active.filter(p => selectedPromoType === 'all' || p.type === selectedPromoType), grid = $('promo-cards-grid');
        grid.replaceChildren(); document.querySelector('.promo-filter-btn').textContent = `Barchasi (${active.length})`;
        if (!items.length) grid.append(el('p', 'text-slate-400 col-span-full text-center py-10', 'Hozircha narxi, shartlari va amal qilish muddati tasdiqlangan taklif yo‘q.'));
        items.forEach(p => {
            const card = el('article', 'glass-card rounded-3xl p-6 space-y-4');
            card.append(el('h3', 'font-bold text-white text-lg', D.text(p.name)), el('p', 'text-emerald-300 text-sm', 'Rasmiy manbada tekshirilgan'), el('p', 'text-slate-300 text-sm', D.text(p.description, 2000)), el('p', 'font-semibold text-cyan-300 text-sm', 'Narx/taklif: ' + D.text(p.price)), el('p', 'text-slate-300 text-sm', 'Shartlar: ' + D.text(p.terms, 5000)), el('p', 'text-amber-300 text-sm', 'Amal qiladi: ' + new Date(p.starts_at).toLocaleString('uz-UZ') + ' — ' + new Date(p.expires_at).toLocaleString('uz-UZ')), el('p', 'text-xs text-slate-400', 'Tekshirilgan: ' + new Date(p.verified_at).toLocaleString('uz-UZ')), link('Rasmiy taklifni ko‘rish', p.url, 'inline-block bg-amber-500 text-slate-950 font-bold px-4 py-2 rounded-xl text-sm'));
            grid.append(card);
        }); $('metric-promos').textContent = active.length;
    }
    function scrollToSection(id) { $(id)?.scrollIntoView({behavior: 'smooth'}); }
    function updateSearch(term) { currentSearch = term; visibleLimit = 24; $('hero-search').value = term; $('catalog-search').value = term; renderCards(); }
    function quickSearch(term) { currentCategory = 'Hammasi'; currentPricing = 'all'; if (term.toLowerCase() === 'bepul') { currentPricing = 'free'; term = ''; } updateSearch(term); scrollToSection('katalog'); }
    function filterByCategory(category) { currentCategory = category; currentPricing = 'all'; updateSearch(''); scrollToSection('katalog'); }
    function resetFilters() { currentCategory = 'Hammasi'; currentPricing = 'all'; updateSearch(''); }
    function appendChatBubble(sender, message, tools = []) {
        const bubble = el('div', sender === 'user' ? 'ml-auto max-w-[85%] px-3.5 py-2.5 rounded-2xl bg-cyan-500 text-slate-950' : 'mr-auto max-w-[92%] px-3.5 py-2.5 rounded-2xl bg-white/10 text-slate-200 border border-white/10 space-y-2', message);
        tools.forEach(ai => { const button = el('button', 'block w-full text-left p-2 rounded-xl bg-dark-950/90 text-cyan-300', ai.name); button.type = 'button'; button.addEventListener('click', () => openModalById(ai.id)); bubble.append(button); });
        $('chat-messages').append(bubble); $('chat-messages').scrollTop = $('chat-messages').scrollHeight;
    }
    function toggleAIChat(force) { const show = force === undefined ? $('ai-chat-window').classList.contains('hidden') : force; $('ai-chat-window').classList.toggle('hidden', !show); if (show && !$('chat-messages').children.length) appendChatBubble('ai', 'Bu yordamchi katalogni kalit so‘zlar orqali qidiradi. AI modeli bilan suhbat emas. Masalan, «video», «kod» yoki vosita nomini yozing.'); }
    function handleChatSubmit(event) {
        event.preventDefault(); const query = $('chat-input').value.trim(); if (!query) return;
        $('chat-input').value = ''; appendChatBubble('user', query); const lower = query.toLowerCase();
        const mapping = [['video', 'Video Generatsiya'], ['kod', 'Dasturlash va Kod'], ['dastur', 'Dasturlash va Kod'], ['rasm', 'Rasm va San’at'], ['ovoz', 'Ovoz va Musiqa'], ['musiqa', 'Ovoz va Musiqa']];
        if (lower.includes('bepul')) { quickSearch('bepul'); appendChatBubble('ai', 'Manbada bepul tarif qayd etilgan vositalar ko‘rsatilmoqda. Joriy narx va cheklovlarni xizmat sahifasida tekshiring.', getFilteredAIs().slice(0, 4)); return; }
        const category = mapping.find(([key]) => lower.includes(key));
        if (category) filterByCategory(category[1]); else quickSearch(query);
        const matches = getFilteredAIs().slice(0, 4);
        appendChatBubble('ai', matches.length ? 'Katalogdan topilgan vositalar:' : 'Katalogdan mos vosita topilmadi. Qisqaroq kalit so‘z yoki vosita nomini yozing.', matches);
    }
    function sendQuickChat(text) { toggleAIChat(true); $('chat-input').value = text; handleChatSubmit({preventDefault() {}}); }
    function getStoredReviews() {
        try { const values = JSON.parse(localStorage.getItem('ai_olami_reviews') || '[]'); return Array.isArray(values) ? values.filter(v => v && typeof v.name === 'string' && typeof v.text === 'string' && Number.isInteger(v.stars) && v.stars >= 1 && v.stars <= 5).slice(0, 50) : []; } catch { return []; }
    }
    function selectReviewStar(value) {
        selectedReviewStars = value; $('selected-star-label').textContent = value + ' yulduz';
        document.querySelectorAll('.star-pick-btn').forEach(button => { const active = Number(button.dataset.star) <= value; button.classList.toggle('text-amber-400', active); button.classList.toggle('text-slate-600', !active); button.setAttribute('aria-label', button.dataset.star + ' yulduz'); });
    }
    function renderSiteReviewsAndRating() {
        const reviews = getStoredReviews(); $('site-reviews-count').textContent = reviews.length;
        $('site-avg-rating').textContent = reviews.length ? (reviews.reduce((sum, r) => sum + r.stars, 0) / reviews.length).toFixed(1) : '—';
        $('site-avg-stars').textContent = reviews.length ? '★'.repeat(Math.round(reviews.reduce((sum, r) => sum + r.stars, 0) / reviews.length)) : '';
        const container = $('site-reviews-list'); container.replaceChildren();
        if (!reviews.length) container.append(el('p', 'text-sm text-slate-400', 'Shu brauzerda saqlangan fikr yo‘q.'));
        reviews.forEach(r => { const card = el('div', 'p-4 rounded-2xl bg-dark-950/75 border border-white/10'); card.append(el('p', 'text-sm font-bold text-white', D.text(r.name, 80)), el('p', 'text-amber-400 text-sm', '★'.repeat(r.stars)), el('p', 'text-sm text-slate-300 mt-2 whitespace-pre-wrap', D.text(r.text, 1500))); container.append(card); });
    }
    function submitSiteReview(event) {
        event.preventDefault(); const name = $('reviewer-name').value.trim().slice(0, 80), text = $('reviewer-comment').value.trim().slice(0, 1500); if (!name || !text) return;
        const reviews = getStoredReviews(); reviews.unshift({name, text, stars: selectedReviewStars});
        try { localStorage.setItem('ai_olami_reviews', JSON.stringify(reviews.slice(0, 50))); } catch { $('review-success-msg').textContent = 'Brauzer saqlashga ruxsat bermadi. Fikr saqlanmadi.'; $('review-success-msg').classList.remove('hidden'); return; }
        $('reviewer-name').value = ''; $('reviewer-comment').value = ''; renderSiteReviewsAndRating(); $('review-success-msg').textContent = 'Baho va fikr shu brauzerda saqlandi.'; $('review-success-msg').classList.remove('hidden');
    }
    async function fetchJSON(path) {
        const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 15000);
        try { const response = await fetch(path, {cache: 'no-store', signal: controller.signal}); if (!response.ok) throw new Error(path + ': HTTP ' + response.status); return await response.json(); } finally { clearTimeout(timer); }
    }
    async function loadData() {
        const [directory, catalog, promotions, status] = await Promise.allSettled([fetchJSON('./data/ai-olami-tools.json'), fetchJSON('./data/approved-ai.json'), fetchJSON('./data/promo-candidates.json'), fetchJSON('./data/monitor-status.json')]);
        aiList = D.dedupeTools([...curated, ...(directory.status === 'fulfilled' ? D.normalizeDirectory(directory.value) : []), ...(catalog.status === 'fulfilled' ? D.normalizeTools(catalog.value) : [])]);
        renderCards(); renderMetrics(); initComparisonSelects();
        if (promotions.status === 'fulfilled') promoData = promotions.value;
        else { promoData = {promotions: []}; console.warn('Aksiyalar yuklanmadi:', promotions.reason); }
        renderPromotions();
        const messages = [];
        if (directory.status === 'fulfilled' && Number.isFinite(Date.parse(directory.value.updated_at))) messages.push('Ochiq katalog yangilangan: ' + new Date(directory.value.updated_at).toLocaleString('uz-UZ'));
        if (directory.status === 'rejected') messages.push('Ochiq katalog yuklanmadi; mavjud tahririy va RSS yozuvlari ko‘rsatilmoqda.');
        if (status.status === 'fulfilled' && Number.isFinite(Date.parse(status.value.last_run_at))) {
            messages.push('So‘nggi avtomatik tekshiruv: ' + new Date(status.value.last_run_at).toLocaleString('uz-UZ'));
            const sources = Array.isArray(status.value.sources) ? status.value.sources : [];
            const failures = sources.filter(s => !['ok', 'success'].includes(s.status));
            if (failures.length) messages.push(`${failures.length} ta manbada xato; oldingi tasdiqlangan katalog saqlandi.`);
            if (Date.now() - Date.parse(status.value.last_run_at) > 10800000) messages.push('Tekshiruv ma’lumoti eskirgan.');
        } else messages.push('So‘nggi tekshiruv vaqti hozircha mavjud emas.');
        if (catalog.status === 'rejected') messages.push('RSS topilmalari yuklanmadi.');
        if (promotions.status === 'rejected') messages.push('Aksiyalar yuklanmadi.');
        messages.push('Har soatda tekshirish rejalashtirilgan; GitHub jadvali kechikishi mumkin.'); $('monitor-summary').textContent = messages.join(' • ');
    }
    Object.assign(window, {openModalById, closeModal, renderComparison, toggleAIChat, handleChatSubmit, sendQuickChat,
        quickSearch, filterByCategory, resetFilters, scrollToSection, selectReviewStar, submitSiteReview,
        loadMoreAIs() { visibleLimit += 40; renderCards(); },
        filterPromos(type, button) { selectedPromoType = type; document.querySelectorAll('.promo-filter-btn').forEach(b => { b.className = 'promo-filter-btn px-3.5 py-2 rounded-lg text-xs font-bold transition ' + (b === button ? 'bg-amber-500 text-slate-950' : 'text-slate-300 hover:text-white'); }); renderPromotions(); }});
    document.querySelectorAll('.cat-btn').forEach(button => button.addEventListener('click', () => { currentCategory = button.dataset.cat; visibleLimit = 24; renderCards(); }));
    priceButtons.forEach(button => button.addEventListener('click', () => { currentPricing = button.dataset.price; visibleLimit = 24; renderCards(); }));
    document.querySelectorAll('[data-stats]').forEach(button => button.addEventListener('click', () => { currentStats = button.dataset.stats; renderStatistics(); }));
    ['search-compare-a', 'search-compare-b'].forEach(id => $(id).addEventListener('input', initComparisonSelects));
    ['catalog-search', 'hero-search'].forEach(id => $(id).addEventListener('input', event => updateSearch(event.target.value)));
    $('hero-search').addEventListener('keydown', event => { if (event.key === 'Enter') scrollToSection('katalog'); });
    $('ai-modal').addEventListener('click', event => { if (event.target === $('ai-modal')) closeModal(); });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') { closeModal(); toggleAIChat(false); }
        if (event.key === 'Tab' && !$('ai-modal').classList.contains('hidden')) {
            const nodes = [...$('ai-modal').querySelectorAll('button, a[href], input, select, textarea')], first = nodes[0], last = nodes[nodes.length - 1];
            if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
            else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
        }
    });
    renderCards(); renderMetrics(); renderPromotions(); initComparisonSelects(); initBrandMarquee(); renderSiteReviewsAndRating(); selectReviewStar(5);
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) initNeuralCanvas();
    loadData(); setInterval(renderPromotions, 60000); document.addEventListener('visibilitychange', () => { if (!document.hidden) renderPromotions(); });
})();
