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
    const directorySources = {
        AGIPicks: 'https://agipicks.com/data/',
        TiorAI: 'https://github.com/tioraicom/ai-tools-dataset',
        AIToolBuzz: 'https://github.com/devadigax/aitoolbuzz-dataset'
    };
    function pricingFlags(tool) {
        const tiers = Array.isArray(tool.pricing_model) ? tool.pricing_model.map(v => text(v, 60).toLowerCase()) : [];
        const free = tool.free_plan === true || tiers.some(v => ['free', 'freemium', 'free tier', 'free plan'].includes(v));
        const paid = tiers.some(v => ['paid', 'subscription', 'pay-as-you-go', 'one-time', 'freemium'].includes(v));
        return {free, paid, opensource: tool.open_source === true, unknown: !free && !paid && tool.open_source !== true};
    }
    function normalizeDirectory(data) {
        if (!data || !Array.isArray(data.tools)) return [];
        return dedupeTools(data.tools.flatMap((item, index) => {
            if (!item || !text(item.name) || !Object.hasOwn(directorySources, item.source) || !categories.includes(item.primary_category)) return [];
            const url = httpsURL(item.official_url);
            if (!url) return [];
            return [{id: 'directory-' + index, name: text(item.name, 180), url, official_url: url,
                category: item.primary_category, description: text(item.short_description) || 'Manba katalogida tavsif berilmagan. Tafsilotlarni xizmat saytida ko‘ring.',
                source: item.source, source_url: directorySources[item.source],
                source_date: text(item.source_date, 64), last_verified: text(item.last_verified, 64),
                pricing_model: Array.isArray(item.pricing_model) ? item.pricing_model.filter(v => typeof v === 'string').map(v => text(v, 60)).slice(0, 4) : [],
                free_plan: typeof item.free_plan === 'boolean' ? item.free_plan : null,
                open_source: item.open_source === true, imported: true, editorial: false, status: 'listed'}];
        }));
    }
    function statistics(tools, view) {
        const count = predicate => tools.filter(predicate).length;
        if (view === 'total') return [
            {title: 'Jami takrorsiz vositalar', value: tools.length},
            {title: 'Tahririy tanlov', value: count(a => a.editorial === true)},
            {title: 'Ochiq kataloglardan', value: count(a => a.imported === true)},
            {title: 'RSS manbalaridan saralangan', value: count(a => !a.editorial && !a.imported)}
        ];
        return categories.map(category => {
            const entries = tools.filter(a => a.category === category);
            const value = view === 'imported' ? entries.filter(a => a.imported).length
                : view === 'free' ? entries.filter(a => pricingFlags(a).free).length
                : view === 'share' ? (tools.length ? entries.length / tools.length * 100 : 0) : entries.length;
            return {title: category, value};
        });
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
    return {categories, text, httpsURL, canonicalURL, normalizedName, dedupeTools, normalizeTools, normalizeDirectory, pricingFlags, statistics, timestamp, activePromotions};
});
