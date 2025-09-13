/**
 * scripts/build-today-updates.js
 * 루트/yourshop/p 폴더에서 최신 5개 HTML을 골라 today-updates.html 생성
 * - 로그 포함(디버깅용)
 */

const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
// 저장소 루트를 BASE로 두고, 실제 글 폴더는 루트/yourshop/p
const BASE_DIR = ROOT;
const POSTS_DIR = path.join('yourshop', 'p');  // 상대 경로로 처리
const OUT_DIR = path.join(ROOT, 'scripts', 'out');
const OUT_FILE = path.join(OUT_DIR, 'today-updates.html');

console.log('[debug] ROOT=', ROOT);
console.log('[debug] POSTS_DIR abs=', path.join(ROOT, POSTS_DIR));
console.log('[debug] POSTS_DIR exists=', fs.existsSync(path.join(ROOT, POSTS_DIR)));

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
    // 2) h1 대체
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
    .slice(0, 80); // 너무 길면 잘라줌
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
  const absPosts = path.join(BASE_DIR, POSTS_DIR);

  if (!fs.existsSync(absPosts)) {
    console.error('yourshop/p 폴더가 없어요. 실제 경로를 확인해 주세요:', absPosts);
    process.exit(0);
  }

  const files = getFilesSortedByMtime(absPosts).slice(0, 5);
  console.log('[debug] picked files=', files.map(f => f.name));

  if (files.length === 0) {
    // 비어 있어도 섹션은 만들어 둔다(빈 리스트)
    console.warn('[warn] yourshop/p 안에 .html 파일을 찾지 못했어요.');
  }

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
