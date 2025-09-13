/**
 * scripts/inject-today-updates.js
 * scripts/out/today-updates.html 내용을 홈( yourshop/index.html 또는 index.md )에 주입
 */
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const BASE_DIR = path.join(ROOT, 'yourshop');
const OUT_SNIPPET = path.join(ROOT, 'scripts', 'out', 'today-updates.html');

const HTML_HOME = path.join(BASE_DIR, 'index.html');
const MD_HOME = path.join(BASE_DIR, 'index.md');

function readSnippet() {
  if (!fs.existsSync(OUT_SNIPPET)) {
    console.error('today-updates.html이 없습니다. 먼저 build-today-updates.js가 생성해야 합니다.');
    process.exit(0);
  }
  return fs.readFileSync(OUT_SNIPPET, 'utf8');
}

function injectToHtml(filePath, snippet) {
  let html = fs.readFileSync(filePath, 'utf8');

  // 기존 섹션 있으면 교체, 없으면 본문 시작부에 삽입
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
    // 최후의 수단: 문서 맨 앞에 붙이기
    html = snippet + '\n' + html;
  }

  fs.writeFileSync(filePath, html, 'utf8');
  console.log('홈(HTML)에 today-updates 섹션 반영:', filePath);
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
  console.log('홈(Markdown)에 today-updates 섹션 반영:', filePath);
}

function main() {
  const snippet = readSnippet();

  if (fs.existsSync(HTML_HOME)) {
    injectToHtml(HTML_HOME, snippet);
    return;
  }
  if (fs.existsSync(MD_HOME)) {
    injectToMarkdown(MD_HOME, snippet);
    return;
  }

  console.error('yourshop/index.html 또는 yourshop/index.md를 찾을 수 없어요.');
  process.exit(0);
}

main();
