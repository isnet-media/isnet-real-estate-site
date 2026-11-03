/* Rendering/schema regression checks. Visual QA: 320, 360, 390, 430 and 768px. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const base = 'sports/ashdod/';
const source = read(base + 'app.js');
const context = vm.createContext({document: {body: {dataset: {}}}, URL});
vm.runInContext(source.slice(0, source.indexOf('function detail(){')), context);
let count = 0;
for (const team of JSON.parse(read(base + 'data.json')).teams) {
  const groups = [
    ...(team.tables || []).map(t => ['table', t.headers, t.rows]),
    ['players', team.players?.headers || [], team.players?.rows || []],
    ['scorers', ['שחקן', 'שערים'], team.scorers?.rows || []],
    ['games', Array.from({length: team.games?.[0]?.values.length || 0}, (_, i) => `נתון ${i + 1}`), team.games || []]
  ];
  for (const [kind, headers, rows] of groups) {
    if (!rows.length) continue;
    Object.assign(context, {team, headers, rows, kind});
    const rendered = vm.runInContext('tab=kind;table(headers,rows,team)', context);
    assert.ok(rendered.includes(`sports-table--${kind}`), `${team.id}: explicit table kind`);
    assert.equal((rendered.match(/<th scope="col">/g) || []).length, headers.length);
    assert.equal((rendered.match(/<td>/g) || []).length, rows.reduce((n, r) => n + r.values.length, 0), `${team.id}: no hidden/dropped data`);
    for (const row of rows) for (const value of row.values) {
      context.value = value;
      assert.ok(rendered.includes(vm.runInContext('esc(value)', context)), `${team.id}: all values preserved`);
    }
    count++;
  }
}
const css = read(base + 'responsive-tables.css');
assert.match(css, /@media \(max-width: 850px\)/);
assert.match(css, /@media \(max-width: 360px\)/);
assert.match(css, /table-layout: fixed/);
assert.match(css, /white-space: normal/);
assert.match(css, /overflow-wrap: break-word/);
assert.match(css, /sports-table--table[\s\S]*:last-child/);
assert.doesNotMatch(css, /(?:th|td)\s*\{[^}]*display:\s*none/, 'never hide a data column');
for (const page of ['index.html','football.html','youth-football.html','basketball.html','handball.html','results.html','teams/ms-ashdod.html','teams/match.html']) {
  const html = read(base + page);
  const styles = [...html.matchAll(/<link[^>]*href="([^\"]+\.css[^\"]*)"[^>]*>/g)];
  assert.match(styles.at(-1)[1], /responsive-tables.css\?v=/, `${page}: shared override must load last`);
  if (html.includes('app.js?')) assert.match(html, /app.js\?v=20261103-tables1/);
  if (html.includes('club.js?')) assert.match(html, /club.js\?v=20261103-tables1/);
}
const club = read(base + 'teams/club.js');
assert.match(club, /class="standings-table"/);
assert.match(club, /class="table-heading-short" title="\$\{x\}"/);
assert.match(club, /class="points-cell"/);
console.log(`PASS: ${count} data-backed tables retain every value; all 8 pages load shared mobile styles and fresh renderers.`);
