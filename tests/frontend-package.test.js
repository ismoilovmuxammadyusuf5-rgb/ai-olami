const test = require('node:test');
const assert = require('node:assert/strict');
const D = require('../assets/site-data.js');

const base = {name: 'Useful AI', official_url: 'https://useful.ai/', primary_category: D.categories[0],
    short_description: 'AI writing tool', source: 'TiorAI', pricing_model: ['Freemium']};

test('directory records need attributed public sources and safe official URLs', () => {
    const records = [base, {...base, name: 'Other', source: '__proto__'},
        {...base, name: 'Unknown', source: 'Untrusted'},
        {...base, name: 'Unsafe', official_url: 'javascript:alert(1)'},
        {...base, name: 'Local', official_url: 'https://localhost/'},
        {...base, name: 'Bad category', primary_category: 'Unmapped'}];
    const result = D.normalizeDirectory({tools: records});
    assert.equal(result.length, 1);
    assert.equal(result[0].source_url, 'https://github.com/tioraicom/ai-tools-dataset');
    assert.equal(result[0].imported, true);
});

test('canonical names and official URLs deduplicate across directory and editorial records', () => {
    const result = D.normalizeDirectory({tools: [base,
        {...base, name: 'USEFUL-AI', official_url: 'https://other.ai/'},
        {...base, name: 'Alternate name', official_url: 'https://www.useful.ai/?utm_source=directory'}]});
    assert.equal(result.length, 1);
    assert.equal(D.dedupeTools([{id: 'curated', name: 'Useful AI', url: 'https://useful.ai/'}, ...result]).length, 1);
});

test('free trials and missing price data do not become free-tier claims', () => {
    assert.equal(D.pricingFlags({pricing_model: ['Free Trial']}).free, false);
    assert.equal(D.pricingFlags({}).unknown, true);
    assert.equal(D.pricingFlags({pricing_model: ['Freemium']}).free, true);
    assert.equal(D.pricingFlags({open_source: 'true'}).opensource, false);
    assert.equal(D.pricingFlags({open_source: true}).opensource, true);
    assert.equal(D.pricingFlags({free_plan: true}).free, true);
    assert.equal(D.pricingFlags({free_plan: false}).unknown, true);
});

test('missing source descriptions remain explicitly unknown instead of hiding real named records', () => {
    const result = D.normalizeDirectory({tools: [{...base, short_description: '', free_plan: true}]});
    assert.equal(result.length, 1);
    assert.match(result[0].description, /tavsif berilmagan/);
    assert.equal(D.pricingFlags(result[0]).free, true);
});

test('all five statistics derive from the actual unique records', () => {
    const directory = D.normalizeDirectory({tools: [base]});
    const tools = [...directory, {id: 'curated', name: 'Editorial', url: 'https://editorial.ai/', category: D.categories[1], editorial: true}];
    assert.equal(D.statistics(tools, 'total')[0].value, 2);
    assert.equal(D.statistics(tools, 'categories').reduce((sum, row) => sum + row.value, 0), 2);
    assert.equal(D.statistics(tools, 'imported').reduce((sum, row) => sum + row.value, 0), 1);
    assert.equal(D.statistics(tools, 'share').reduce((sum, row) => sum + row.value, 0), 100);
    assert.equal(D.statistics(tools, 'free').reduce((sum, row) => sum + row.value, 0), 1);
    assert.equal(D.statistics([], 'share').every(row => row.value === 0), true);
});
