// scripts/build-sitemaps.js
const fs = require('fs');
const path = require('path');

const SITE = 'https://rkskqdl-a11y.github.io/yourshop';
const ROOT = process.cwd();
const P_DIR = path.join(ROOT, 'p');
const OUT_DIR = ROOT;
const CHUNK_SIZE = 1000;

function iso(dt = new Date()) {
  return new Date(dt).toISOString().replace(/\.\d{3}Z$/, 'Z');
}
function xmlEscape(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function findPages() {
  if (!fs.existsSync(P_DIR)) return [];
  return fs.readdirSync(P_DIR)
    .filter(f => f.endsWith('.md'))
    .map(f => {
      const id = f.replace(/\.md$/, '');
      return { loc: `${SITE}/p/${id}.html`, lastmod: iso() };
    });
}
function buildUrlset(urls) {
  const items = urls.map(u => `  <url>
    <loc>${xmlEscape(u.loc)}</loc>
    <lastmod>${u.lastmod}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>`).join('\n\n');
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="https://www.sitemaps.org/schemas/sitemap/0.9">
${items}
</urlset>
`;
}
function buildIndex(files) {
  const stamp = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
  const items = files.map(name => `  <sitemap>
    <loc>${xmlEscape(`${SITE}/${name}`)}</loc>
    <lastmod>${stamp}</lastmod>
  </sitemap>`).join('\n\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<!-- build: ${stamp} -->
<sitemapindex xmlns="https://www.sitemaps.org/schemas/sitemap/0.9">
${items}
</sitemapindex>
`;
}
function write(rel, content) {
  fs.writeFileSync(path.join(OUT_DIR, rel), content, 'utf-8');
  console.log(`[sitemap] wrote: ${rel}`);
}
function main() {
  const pages = findPages();
  pages.unshift({ loc: `${SITE}/`, lastmod: iso() });
  if (pages.length === 0) {
    console.log('[sitemap] no pages found');
    return;
  }
  const chunks = [];
  for (let i = 0; i < pages.length; i += CHUNK_SIZE) {
    chunks.push(pages.slice(i, i + CHUNK_SIZE));
  }
  const files = [];
  chunks.forEach((chunk, i) => {
    const name = chunks.length === 1 ? 'sitemap.xml' : `sitemap-${i + 1}.xml`;
    write(name, buildUrlset(chunk));
    files.push(name);
  });
  write('sitemap_index.xml', buildIndex(files));

  const robotsPath = path.join(OUT_DIR, 'robots.txt');
  let robots = fs.existsSync(robotsPath)
    ? fs.readFileSync(robotsPath, 'utf-8')
    : 'User-agent: *\nAllow: /\n';
  const line = `Sitemap: ${SITE}/sitemap_index.xml`;
  if (!robots.includes(line)) {
    robots = robots.trim() + '\n' + line + '\n';
    fs.writeFileSync(robotsPath, robots, 'utf-8');
    console.log('[sitemap] ensured robots.txt has sitemap_index.xml');
  }
}
main();
