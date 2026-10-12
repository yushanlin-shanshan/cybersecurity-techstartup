import test from 'node:test';
import assert from 'node:assert/strict';
import {formatSummary} from '../dist/summary.js';

test('formats the provider heading and nested-list response',()=>{
 const result=formatSummary('Overview.\n\n### Observations:\n1. **Connection attempts**:\n   - Check `sshd` records.\n\n2. **Server error**:\n   - A 500 response.\n\n### Uncertainty\nNot confirmed.');
 assert.match(result,/<h3>Observations:<\/h3><ol><li><p><strong>Connection attempts<\/strong>:/);
 assert.match(result,/<ul><li><p>Check <code>sshd<\/code> records\.<\/p><\/li><\/ul>/);
 assert.match(result,/<\/ol><h3>Uncertainty<\/h3><p>Not confirmed\.<\/p>/);
});
test('never renders HTML or links from untrusted summaries',()=>{
 const result=formatSummary('**<img src=x onerror=alert(1)>**\n\n<script>alert(1)</script>\n\n[open](javascript:alert(1))');
 assert.ok(!result.includes('<img')&&!result.includes('<script')&&!result.includes('<a'));
 assert.match(result,/&lt;img/);
});
test('keeps full long explanations accessible while short summaries stay visible',()=>{
 const long='Overview.\n\n### Observations\n'+('Evidence needs review. '.repeat(70));
 const result=formatSummary(long);
 assert.match(result,/^<p>Overview\.<\/p><details class="summary-more">/);
 assert.equal((result.match(/Evidence needs review\./g)||[]).length,70);
 assert.equal(formatSummary('Short plain summary.'),'<p>Short plain summary.</p>');
});
