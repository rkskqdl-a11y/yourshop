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
    const text = (title || name.replace(/\.html$/i, '')).replace(/\s+/g,' ').trim();
    return [
      '    <li class="tu-item">',
      `      <a class="tu-link" href="${url}" aria-label="${text} 열기">`,
      '        <span class="tu-bullet" aria-hidden="true"></span>',
      '        <span class="tu-main">',
      `          <span class="tu-title">${text}</span>`,
      '          <span class="tu-meta">방금 업데이트 · 추천</span>',
      '        </span>',
      '        <span class="tu-arrow" aria-hidden="true">↗</span>',
      '      </a>',
      '    </li>'
    ].join('\n');
  }).join('\n');

  return [
    '<section id="today-updates" class="today-updates" style="margin:24px 0;">',
    '  <div class="tu-head">',
    '    <h2>오늘 업데이트</h2>',
    '    <a class="tu-more" href="/yourshop/p/" aria-label="최근 업데이트 더 보기">최근 30개 보기</a>',
    '  </div>',
    '  <ul class="tu-list">',
    items,
    '  </ul>',
    '  <style>',
    '    .today-updates{--fg:#e6f1ff;--fg-dim:#a9b4c8;--accent:#4da3ff;--hover:#7fc1ff;--line:#2b3240;--bgchip:#1f2630;}',
    '    .today-updates .tu-head{display:flex;align-items:center;justify-content:space-between;margin:0 0 12px;}',
    '    .today-updates h2{font-size:1.1rem;margin:0;color:var(--fg);}',
    '    .today-updates .tu-more{font-size:.8rem;color:var(--fg-dim);text-decoration:none;border:1px solid var(--line);padding:3px 8px;border-radius:999px;background:var(--bgchip);} ',
    '    .today-updates .tu-more:hover{color:var(--hover);border-color:var(--hover);} ',
    '    .today-updates .tu-list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:8px;}',
    '    .today-updates .tu-item{border:1px solid var(--line);border-radius:10px;background:rgba(255,255,255,0.02);} ',
    '    .today-updates .tu-link{display:flex;align-items:center;gap:10px;padding:10px 12px;text-decoration:none;color:var(--fg);} ',
    '    .today-updates .tu-bullet{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px rgba(77,163,255,.12);} ',
    '    .today-updates .tu-main{display:flex;flex-direction:column;gap:4px;min-width:0;flex:1;}',
    '    .today-updates .tu-title{display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden;text-overflow:ellipsis;white-space:normal;}',
    '    .today-updates .tu-meta{font-size:.78rem;color:var(--fg-dim);} ',
    '    .today-updates .tu-arrow{color:var(--fg-dim);transition:transform .15s ease,color .15s ease;}',
    '    .today-updates .tu-link:hover .tu-arrow{transform:translateY(-1px) translateX(2px);color:var(--hover);} ',
    '    .today-updates .tu-link:hover .tu-title{color:var(--hover);} ',
    '    .today-updates .tu-item:focus-within{outline:2px solid var(--accent);outline-offset:2px;border-radius:10px;}',
    '    @media (max-width:480px){.today-updates .tu-meta{display:none;}}',
    '  </style>',
    '</section>'
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
