/**
 * scripts/build-today-updates.js
 * yourshop 폴더에서 최신 5개 HTML을 골라 today-updates.html 생성
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const BASE_DIR = path.join(ROOT, 'yourshop');
const POSTS_DIR = path.join(BASE_DIR, 'p');
const OUT_DIR = path.join(ROOT, 'scripts', 'out');
const OUT_FILE = path.join(OUT_DIR, 'today-updates.html');

console.log('[debug] ROOT=', ROOT);
console.log('[debug] POSTS_DIR exists=', fs.existsSync(POSTS_DIR), POSTS_DIR);

function getFilesSortedByMtime(dir, ext = '.html') {
  if (!fs.existsSync(dir)) return [];
  const files = fs.readdirSync(dir)
    .filter(f => f.endsWith(ext))
    .map(f => {
      const full = path.join(dir, f);
      const stat = fs.statSync(full);
      return { name: f, full, mtime: stat.mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime);
  return files;
}

function buildSection(latest) {
  const items = latest.map(({ name, title }) => {
    const url = `/yourshop/p/${name}`;
    const text = title || name.replace(/\.html$/, '');
    return `    <li><a href="${url}">${text}</a></li>`;
  }).join('\n');

  return [
    '<section id="today-updates" style="margin:24px 0;">',
    '  <h2 style="font-size:1.25rem; margin-bottom:12px;">오늘 업데이트</h2>',
    '  <ul>',
    items,
    '  </ul>',
    '</section>',
  ].join('\n');
}

function extractTitle(htmlPath) {
  try {
    const html = fs.readFileSync(htmlPath, 'utf8');
    const m = html.match(/<title>([^<]+)<\/title>/i);
    if (m && m[1]) return m[1].trim();
  } catch (_) {}
  return null;
}

function main() {
  if (!fs.existsSync(POSTS_DIR)) {
    console.error('yourshop/p 폴더가 없어요.');
    process.exit(0);
  }
  const files = getFilesSortedByMtime(POSTS_DIR).slice(0, 5);
  console.log('[debug] picked files=', files.map(f => f.name));
  const withTitles = files.map(f => ({
    ...f,
    title: extractTitle(f.full),
  }));

  const html = buildSection(withTitles);

  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });
  fs.writeFileSync(OUT_FILE, html, 'utf8');
  console.log('generated:', OUT_FILE);
}

main();
