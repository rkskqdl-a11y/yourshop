/**
 * scripts/build-today-updates.js
 * 최신 5개 HTML을 찾아 today-updates.html 조각을 생성
 * - 기본 경로: 루트/yourshop/p
 * - 안전판: yourshop/p 없으면 루트/p, 루트/site/yourshop/p 순서로 탐색
 * - 디버그 로그 포함
 */

const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();

// 후보 경로들을 순서대로 검사해서 실제 존재하는 경로를 선택
const candidates = [
  path.join(ROOT, 'yourshop', 'p'),
  path.join(ROOT, 'p'),
  path.join(ROOT, 'site', 'yourshop', 'p'),
];

let POSTS_DIR = null;
for (const c of candidates) {
  if (fs.existsSync(c)) {
    POSTS_DIR = c;
    break;
  }
}

// 디버그 로그
console.log('[debug] ROOT=', ROOT);
console.log('[debug] candidates=', candidates);
console.log('[debug] resolved POSTS_DIR=', POSTS_DIR);

if (!POSTS_DIR) {
  console.error('[error] 글 폴더(p)를 찾지 못했습니다. 아래 경로들을 확인해 주세요:');
  for (const c of candidates) console.error(' - ' + c);
  process.exit(1);
}

const OUT_DIR = path.join(ROOT, 'scripts', 'out');
const OUT_FILE = path.join(OUT_DIR, 'today-updates.html');

function getFilesSortedByMtime(absDir, ext = '.html') {
  if (!fs.existsSync(absDir)) return [];
  const files = fs.readdirSync(absDir)
    .filter(f => f.toLowerCase().endsWith(ext))
    .map(f => {
      const full = path.join(absDir, f);
      const stat = fs.statSync(full);
      return { name: f, full, mtime: stat.mtimeMs };
    })
    .sort((a, b) => b.mtime - a.mtime);
  return files;
}

function extractTitle(htmlPath) {
  try {
    const html = fs.readFileSync(htmlPath, 'utf8');
    // 1) <title> 우선
    let m = html.match(/<title>([^<]+)<\/title>/i);
    if (m && m[1]) return sanitize(m[1]);
    // 2) <h1> 대체
    m = html.match(/<h1[^>]*>([^<]+)<\/h1>/i);
    if (m && m[1]) return sanitize(m[1]);
  } catch (e) {
    // ignore
  }
  return null;
}

function sanitize(text) {
  return String(text)
    .replace(/\s+/g, ' ')
    .replace(/[\r\n\t]/g, ' ')
    .trim()
    .slice(0, 80);
}

function buildSection(latest) {
  const items = latest.map(({ name, title }) => {
    const url = `/yourshop/p/${name}`;
    const text = title || name.replace(/\.html$/i, '');
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
function main() {
  const files = getFilesSortedByMtime(POSTS_DIR).slice(0, 5);
  console.log('[debug] picked files=', files.map(f => f.name));

  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

  const withTitles = files.map(f => ({
    ...f,
    title: extractTitle(f.full),
  }));

  const html = buildSection(withTitles);
  fs.writeFileSync(OUT_FILE, html, 'utf8');
  console.log('generated:', OUT_FILE);
}

main();
