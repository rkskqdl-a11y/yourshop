// scripts/gen-sitemap.js (프로젝트 페이지용: 퍼블릭 접두사 /yourshop 반영)
// 목적: 루트의 p/*.html + 허브(/yourshop/)를 포함해 루트 /sitemap.xml 자동 생성
// lastmod: 각 파일의 마지막 커밋 시간(없으면 현재 시각)

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

// GitHub Pages 프로젝트 페이지 기본값
const BASE = 'https://rkskqdl-a11y.github.io'; // 사용자 도메인
const REPO = 'yourshop';                        // 이 레포 이름(퍼블릭 접두사)
const PUBLIC_PREFIX = `/${REPO}`;               // "/yourshop"

const PAGES_DIR = path.resolve('p');            // 루트의 p/ 폴더
const SITEMAP_PATH = path.resolve('sitemap.xml'); // 루트에 생성

async function walkHtmlFiles(dir) {
  const out = [];
  let entries = [];
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return out; // 폴더가 없을 수도 있음
  }
  for (const it of entries) {
    const p = path.join(dir, it.name);
    if (it.isDirectory()) {
      const nested = await walkHtmlFiles(p);
      out.push(...nested);
    } else if (it.isFile() && it.name.toLowerCase().endsWith('.html')) {
      out.push(p);
    }
  }
  return out;
}

function gitLastCommitIso(filePath) {
  try {
    const iso = execSync(`git log -1 --pretty=format:%cI -- "${filePath}"`, { encoding: 'utf8' }).trim();
    if (iso) return iso;
  } catch {}
  return new Date().toISOString();
}

function toPublicUrl(filePath) {
  // 파일 경로를 퍼블릭 URL로 변환 (프로젝트 페이지는 /{repo}/ 접두사 필요)
  const unix = filePath.split(path.sep).join('/'); // OS 구분자 통일
  return `${BASE}${PUBLIC_PREFIX}/${unix}`;
}

function xmlEscape(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function main() {
  // 허브 URL(컬렉션 페이지)
  const hub = {
    loc: `${BASE}${PUBLIC_PREFIX}/`,
    lastmod: new Date().toISOString(),
    changefreq: 'hourly',
    priority: '1.0',
  };

  // p/ 밑의 html 수집
  const files = await walkHtmlFiles(PAGES_DIR);

  const urls = files.map(fp => ({
    loc: toPublicUrl(fp),
    lastmod: gitLastCommitIso(fp),
    changefreq: 'daily',
    priority: '0.8',
  }));

  // 최신순 정렬(선택)
  urls.sort((a, b) => (a.lastmod < b.lastmod ? 1 : -1));

  const nodes = [
    `<url>
  <loc>${xmlEscape(hub.loc)}</loc>
  <lastmod>${hub.lastmod}</lastmod>
  <changefreq>${hub.changefreq}</changefreq>
  <priority>${hub.priority}</priority>
</url>`,
    ...urls.map(u => `<url>
  <loc>${xmlEscape(u.loc)}</loc>
  <lastmod>${u.lastmod}</lastmod>
  <changefreq>${u.changefreq}</changefreq>
  <priority>${u.priority}</priority>
</url>`),
  ].join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${nodes}
</urlset>
`;

  await fs.writeFile(SITEMAP_PATH, xml, 'utf8');
  console.log(`Generated sitemap.xml with ${urls.length + 1} URLs (including hub)`);
}

main().catch(e => {
  console.error(e);
  process.exit(1);
});
