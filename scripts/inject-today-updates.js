/**
 * scripts/inject-today-updates.js
 * today-updates.html 조각을 홈에 주입
 * 우선순위:
 * 1) yourshop/index.html
 * 2) yourshop/index.md
 * 3) 루트/index.html
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const BASE_DIR = path.join(ROOT, 'yourshop');
const OUT_SNIPPET = path.join(ROOT, 'scripts', 'out', 'today-updates.html');

const CANDIDATES = [  path.join(BASE_DIR, 'index.html'),  path.join(BASE_DIR, 'index.md'),  path.join(ROOT, 'index.html'),];

function readSnippet() {
  if (!fs.existsSync(OUT_SNIPPET)) {
    console.error('today-updates.html이 없습니다. 먼저 build-today-updates.js를 실행하세요.');
    process.exit(1);
  }
  return fs.readFileSync(OUT_SNIPPET, 'utf8');
}

function injectToHtml(filePath, snippet) {
  let html = fs.readFileSync(filePath, 'utf8');
  if (html.includes('<section id="today-updates"')) {
    html = html.replace(
      /<section id="today-updates"[\s\S]*?<\/section>/,
      snippet
    );
  } else if (html.includes('</header>')) {
    html = html.replace('</header>', '</header>\n' + snippet + '\n');
  } else if (html.match(/<main[^>]*>/)) {
    html = html.replace(/<main[^>]*>/, m => m + '\n' + snippet + '\n');
  } else if (html.includes('<body>')) {
    html = html.replace('<body>', '<body>\n' + snippet + '\n');
  } else {
    html = snippet + '\n' + html;
  }
  fs.writeFileSync(filePath, html, 'utf8');
  console.log('홈(HTML)에 today-updates 섹션 반영:', path.relative(ROOT, filePath));
}

function injectToMarkdown(filePath, snippet) {
  let md = fs.readFileSync(filePath, 'utf8');
  if (md.includes('<section id="today-updates"')) {
    md = md.replace(
      /<section id="today-updates"[\s\S]*?<\/section>/,
      snippet
    );
  } else {
    if (md.startsWith('---')) {
      const end = md.indexOf('---', 3);
      if (end !== -1) {
        const front = md.slice(0, end + 3);
        const body = md.slice(end + 3);
        md = front + '\n\n' + snippet + '\n\n' + body;
      } else {
        md = snippet + '\n\n' + md;
      }
    } else {
      md = snippet + '\n\n' + md;
    }
  }
  fs.writeFileSync(filePath, md, 'utf8');
  console.log('홈(Markdown)에 today-updates 섹션 반영:', path.relative(ROOT, filePath));
}

function main() {
  const snippet = readSnippet();
  const existing = CANDIDATES.filter(p => fs.existsSync(p));

  if (existing.length === 0) {
    console.error('yourshop/index.html, yourshop/index.md, 루트/index.html 중 어떤 것도 찾지 못했습니다.');
    process.exit(1);
  }

  const target = existing[0];
  if (target.endsWith('.md')) {
    injectToMarkdown(target, snippet);
  } else {
    injectToHtml(target, snippet);
  }
}

main();
