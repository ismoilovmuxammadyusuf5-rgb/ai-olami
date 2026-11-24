(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.AIOlamiData = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';
    const categories = ['Katta Til Modellari', 'Rasm va San’at', 'Video Generatsiya', 'Ovoz va Musiqa', 'Dasturlash va Kod', 'Qidiruv va Tadqiqot', 'Dizayn va 3D', 'Avtomatlashtirish'];
    const text = (value, max = 1600) => typeof value === 'string' ? value.trim().slice(0, max) : '';
    function httpsURL(value) {
        try {
            const url = new URL(value);
            const host = url.hostname.toLowerCase();
            const publicName = /^[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$/.test(host) && host.includes('.') && !host.endsWith('.local') && !host.endsWith('.internal') && !host.endsWith('.localhost');
            const ipv4 = /^\d+\.\d+\.\d+\.\d+$/.test(host);
            return url.protocol === 'https:' && !url.username && !url.password && !url.port && publicName && !ipv4 ? url.href : '';
        } catch { return ''; }
    }
    function canonicalURL(value) {
        const safe = httpsURL(value);
        if (!safe) return '';
        const url = new URL(safe);
        return url.hostname.toLowerCase().replace(/^www\./, '') + url.pathname.replace(/\/+$/, '').toLowerCase();
    }
    function normalizedName(value) {
        return text(value).normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');
    }
    function dedupeTools(tools) {
        const names = new Set(), urls = new Set(), ids = new Set();
        return tools.filter(tool => {
            const name = normalizedName(tool.name), url = canonicalURL(tool.url);
            if (!name || !url || names.has(name) || urls.has(url) || ids.has(tool.id)) return false;
            names.add(name); urls.add(url); ids.add(tool.id); return true;
        });
    }
    function normalizeTools(data) {
        if (!data || data.schema_version !== 1 || !Array.isArray(data.tools)) return [];
        return dedupeTools(data.tools.flatMap((item, index) => {
            if (!item || item.status !== 'approved' || !text(item.name) || !text(item.description) || !categories.includes(item.category)) return [];
            const url = httpsURL(item.url), sourceURL = httpsURL(item.source_url);
            if (!url || !sourceURL || !item.evidence) return [];
            return [{id: 'discovered-' + (text(item.id, 160) || index), name: text(item.name, 180), url,
                description: text(item.description), category: item.category, source: text(item.source, 100) || 'Ochiq manba',
                source_url: sourceURL, official_url: httpsURL(item.official_url), evidence: item.evidence,
                approved_at: text(item.approved_at, 64), status: 'approved', editorial: false}];
        }));
    }
    function timestamp(value) {
        if (typeof value !== 'string') return NaN;
        const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(Z|[+-]\d{2}:\d{2})$/i.exec(value);
        if (!match) return NaN;
        const [, year, month, day, hour, minute, second, zone] = match;
        const monthDays = new Date(Date.UTC(Number(year), Number(month), 0)).getUTCDate();
        if (Number(year) < 1970 || Number(month) < 1 || Number(month) > 12 || Number(day) < 1 || Number(day) > monthDays || Number(hour) > 23 || Number(minute) > 59 || Number(second) > 59) return NaN;
        if (zone !== 'Z' && zone !== 'z' && (Number(zone.slice(1, 3)) > 14 || Number(zone.slice(4)) > 59 || (Number(zone.slice(1, 3)) === 14 && Number(zone.slice(4)) !== 0))) return NaN;
        return Date.parse(value);
    }
    function activePromotions(data, now = Date.now()) {
        if (!data || !Array.isArray(data.promotions)) return [];
        return data.promotions.filter(p => {
            if (!p || p.status !== 'approved' || !['trial', 'bonus', 'discount'].includes(p.type)) return false;
            if (!text(p.name) || !text(p.price) || !text(p.terms) || !p.evidence || typeof p.evidence !== 'object') return false;
            if (p.terms.length > 5000 || (typeof p.description === 'string' && p.description.length > 2000)) return false;
            const start = timestamp(p.starts_at), end = timestamp(p.expires_at), verified = timestamp(p.verified_at);
            if (![start, end, verified].every(Number.isFinite) || start > now || end <= now || start >= end || verified > now + 60000 || now - verified > 86400000) return false;
            const trusted = {OpenAI: ['openai.com', 'www.openai.com'], Google: ['blog.google', 'www.blog.google']};
            const domain = text(p.official_domain).toLowerCase(), url = httpsURL(p.url), evidenceURL = httpsURL(p.evidence.url);
            if (!domain || !url || !evidenceURL || url !== evidenceURL || !trusted[p.source]?.includes(domain) || new URL(url).hostname.toLowerCase() !== domain || new URL(evidenceURL).hostname.toLowerCase() !== domain) return false;
            return ['price', 'terms', 'starts_at', 'expires_at'].every(field => text(p.evidence[field]) && p.evidence[field] === p[field]);
        });
    }
    return {categories, text, httpsURL, canonicalURL, normalizedName, dedupeTools, normalizeTools, timestamp, activePromotions};
});
