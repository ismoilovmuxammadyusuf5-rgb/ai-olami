const test = require('node:test');
const assert = require('node:assert/strict');
const D = require('../assets/site-data.js');
const now = Date.parse('2026-11-24T12:00:00Z');

function promotion(changes = {}) {
    const promo = {name: 'Test AI trial', source: 'OpenAI', status: 'approved', type: 'trial',
        url: 'https://openai.com/offer', official_domain: 'openai.com', price: '0 USD',
        terms: 'Eligible new users', starts_at: '2026-11-01T00:00:00Z',
        expires_at: '2026-12-01T00:00:00Z', verified_at: '2026-11-24T11:00:00Z'};
    promo.evidence = {url: promo.url, price: promo.price, terms: promo.terms,
        starts_at: promo.starts_at, expires_at: promo.expires_at};
    return {...promo, ...changes};
}
const active = promo => D.activePromotions({promotions: [promo]}, now);

test('complete active official promotion displays with its matching evidence', () => {
    assert.equal(active(promotion()).length, 1);
});

test('uncertain, expired, future, or stale promotions fail closed', () => {
    for (const changes of [
        {status: 'pending'}, {status: 'rejected'},
        {verified_at: '2026-11-23T11:00:00Z'}, {verified_at: '2026-11-25T11:00:00Z'},
        {expires_at: '2026-11-23T00:00:00Z'}, {starts_at: '2026-11-25T00:00:00Z'},
        {starts_at: '2026-11-01'}, {expires_at: '2027-02-30T00:00:00Z'},
        {terms: ''}, {price: ''}, {type: 'unknown'},
    ]) assert.deepEqual(active(promotion(changes)), [], JSON.stringify(changes));
});

test('self declared official domains, unsafe links, and mismatched evidence are hidden', () => {
    const base = promotion();
    for (const changes of [
        {url: 'https://openai.com.evil.org/offer'}, {url: 'javascript:alert(1)'},
        {official_domain: 'evil.org', url: 'https://evil.org/'}, {source: 'Unknown'},
        {url: 'https://user:secret@openai.com/'}, {url: 'https://openai.com:444/'},
        {evidence: {...base.evidence, price: '1 USD'}},
        {evidence: {...base.evidence, terms: 'A different offer'}},
        {evidence: {...base.evidence, url: 'https://evil.org/proof'}},
        {evidence: {...base.evidence, url: 'https://openai.com/another-offer'}},
    ]) assert.deepEqual(active(promotion(changes)), [], JSON.stringify(changes));
});

test('complete promotion restrictions are preserved and oversized terms fail closed', () => {
    const terms = 'Restriction '.repeat(350);
    const promo = promotion({terms});
    promo.evidence.terms = terms;
    assert.equal(active(promo).length, 1);
    assert.equal(D.text(active(promo)[0].terms, 5000), terms.trim());
    const oversized = promotion({terms: 'X'.repeat(5001)});
    oversized.evidence.terms = oversized.terms;
    assert.equal(active(oversized).length, 0);
});

test('date validation rejects calendar overflow, absent timezone, and invalid offsets', () => {
    for (const value of ['2026-02-30T00:00:00Z', '2026-02-29T00:00:00Z', '2026-11-24',
        '2026-11-24T00:00:00', '2026-11-24T24:00:00Z', '2026-11-24T00:00:00+14:01']) {
        assert(Number.isNaN(D.timestamp(value)), value);
    }
    assert(Number.isFinite(D.timestamp('2028-02-29T00:00:00+05:00')));
});

test('public HTTPS validation rejects local, IP, credentials, and custom ports', () => {
    for (const value of ['https://127.0.0.1/test', 'https://localhost/test', 'https://local.internal/',
        'https://0x7f000001/', 'http://example.com/', 'https://user:secret@example.com/',
        'https://example.com:444/']) assert.equal(D.httpsURL(value), '', value);
    assert.equal(D.httpsURL('https://www.example.com/path'), 'https://www.example.com/path');
});

test('approved discoveries merge once per canonical name or URL and unsafe records are excluded', () => {
    const tool = {id: 'example', name: 'Example', url: 'https://example.com/',
        source_url: 'https://producthunt.com/products/example', source: 'Product Hunt',
        description: 'AI assistant for coding', category: 'Dasturlash va Kod',
        status: 'approved', evidence: {excerpt: 'AI assistant for coding'}};
    const tools = D.normalizeTools({schema_version: 1, tools: [tool,
        {...tool, id: 'duplicate', name: 'EXAMPLE', url: 'https://www.example.com/?utm_source=test'},
        {...tool, status: 'pending', id: 'pending'},
        {...tool, id: 'unsafe', name: 'Unsafe', url: 'javascript:alert(1)'},
        {...tool, id: 'unknown', name: 'Unknown', category: 'Unmapped'},
    ]});
    assert.equal(tools.length, 1);
    assert.equal(tools[0].name, 'Example');
    assert.deepEqual(D.normalizeTools({schema_version: 2, tools: [tool]}), []);
});
