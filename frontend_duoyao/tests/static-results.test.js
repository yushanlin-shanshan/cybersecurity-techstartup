import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateResults} from '../dist/schema.js';

const config = JSON.parse(readFileSync(new URL('../dist/app-config.json', import.meta.url)));
const results = validateResults(JSON.parse(readFileSync(new URL('../dist/api-static/results.json', import.meta.url))));

test('published config points at the static demo snapshot', () => {
  assert.equal(config.job_id, 'demo');
  assert.equal(config.results_url, '/api-static/results.json');
});

test('static snapshot matches the schema and keeps evidence ids unique', () => {
  assert.equal(results.mode, 'results');
  assert.equal(results.incidents.length, 1825);
  assert.equal(results.dataset.name, 'russellmitchell');
  for (const incident of results.incidents) {
    assert.ok(incident.evidence.length > 0);
    assert.equal(new Set(incident.evidence.map(item => item.id)).size, incident.evidence.length);
  }
  assert.ok(results.incidents.every((item, index) => index === 0 || item.score <= results.incidents[index - 1].score));
});
