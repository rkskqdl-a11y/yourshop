// scripts/gen-sitemap.js (프로젝트 페이지용: 퍼블릭 접두사 /yourshop, 상대경로로 URL 생성)
// 문제 원인: 절대 경로(/home/runner/…)가 URL에 들어감 → 상대 경로(p/..html)로 바꿔 해결
// lastmod: 파일의 마지막 커밋 시간(없으면 현재 시각)

const fs = require('fs').promises;
const path = require('path');
const { execSync } = require('child_process');

// GitHub Pages 프로젝트 페이지 기준
const BASE = 'https://rkskqdl-a11y.github.io';
const REPO = 'yourshop';
const PUBLIC_PREFIX = `/${REPO}`; // "/yourshop"

// 레포 루트 기준 경로
const PAGES_DIR = 'p';           // 루트의 p/ 폴더 (상대 경로 사용)
const SITEMAP_PATH = 'sitemap.xml';

// p/ 아래 HTML을 "레포 루트 기준 상대 경로"로 수집
async function walkHtmlFiles(relDir) {
  const out = [];
  let entries = [];
  try {
    entries = await fs.readdir(relDir, { withFileTypes: true });
  } catch {
    return out; // 폴더 없으면 빈 배열
  }
  for (const it of entries) {
    const nextRel = path.join(relDir, it.name); // 항상 상대 경로 유지
    if (it.isDirectory()) {
      const nested = await walkHtmlFiles(nextRel);
      out.push(...nested);
    } else if (it.isFile() && it.name.toLowerCase().endsWith('.html')) {
      out.push(nextRel);
    }
  }
  return out;
}

// 파일의 마지막 커밋 시간을 ISO로
function gitLastCommitIso(relPath) {
  try {
    const iso = execSync(`git log -1 --pretty=format:%cI -- "${relPath}"`, { encoding: 'utf8' }).trim();
    if (iso) return iso;
  } catch {}
  return new Date().toISOString();
}

// 상대 경로 → 퍼블릭 URL
function toPublicUrl(relPath) {
  const unix = relPath.split(path.sep).join('/'); // "p/xxx.html"
  // 최종: https://.../yourshop/p/xxx.html
  return `${BASE}${PUBLIC_PREFIX}/${unix}`;
}

function xmlEscape(s) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

async function main() {
  // 허브(/yourshop/) 먼저
  const hub = {
    loc: `${BASE}${PUBLIC_PREFIX}/`,
    lastmod: new Date().toISOString(),
    changefreq: 'hourly',
    priority: '1.0',
  };

  const files = await walkHtmlFiles(PAGES_DIR); // 상대 경로 리스트
  const urls = files.map((rel) => ({
    loc: toPublicUrl(rel),
    lastmod: gitLastCommitIso(rel),
    changefreq: 'daily',
    priority: '0.8',
  }));

  // 최신순(선택)
  urls.sort((a, b) => (a.lastmod < b.lastmod ? 1 : -1));

  const nodes = [
    `<url>
  <loc>${xmlEscape(hub.loc)}</loc>
  <lastmod>${hub.lastmod}</lastmod>
  <changefreq>${hub.changefreq}</changefreq>
  <priority>${hub.priority}</priority>
</url>`,
    ...urls.map(
      (u) => `<url>
  <loc>${xmlEscape(u.loc)}</loc>
  <lastmod>${u.lastmod}</lastmod>
  <changefreq>${u.changefreq}</changefreq>
  <priority>${u.priority}</priority>
</url>`
    ),
  ].join('\n');

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${nodes}
</urlset>
`;

  await fs.writeFile(SITEMAP_PATH, xml, 'utf8');
  console.log(`Generated sitemap.xml with ${urls.length + 1} URLs (including hub)`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
