// scripts/generate-pages.js
const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const DATA = path.join(ROOT, 'data', 'products.json');
const OUT_DIR = path.join(ROOT, 'p');

function digitsOnly(s) {
  return String(s || '').replace(/[^0-9]/g, '');
}
function sanitize(s) {
  return String(s == null ? '' : s).trim().replace(/\s+/g, ' ').replace(/"/g, '\\"');
}

function frontMatter(item) {
  const title = sanitize(item.title);
  const product_id = String(item.product_id || item.pageKey || item.id || '').trim();
  const image_url = sanitize(item.image_url || '');
  const description = sanitize(item.description || '');
  const brand = sanitize(item.brand || '쿠팡');
  const price_number = digitsOnly(item.price_number || item.price || '');
  const rating_value = (item.rating_value ?? '').toString().trim();
  const review_count = (item.review_count ?? '').toString().trim();

  const ratingBlock = (rating_value && review_count)
    ? `rating_value: "${rating_value}"
review_count: "${review_count}"
`
    : '';

  return `---
layout: product
title: "${title}"
product_id: ${product_id}
image_url: "${image_url}"
description: "${description}"
brand: "${brand}"
price_number: "${price_number}"
${ratingBlock}---
`;
}

function body(item) {
  const description = sanitize(item.description || '');
  const brand = sanitize(item.brand || '쿠팡');
  const product_id = String(item.product_id || '');
  const price_number = digitsOnly(item.price_number || '');

  return `<!-- 본문(자동 생성) -->
<h2>요약</h2>
<p>${description}</p>

<ul>
  <li>브랜드: ${brand}</li>
  <li>상품번호: ${product_id}</li>
  <li>가격: ${price_number}원</li>
</ul>

<p>가격·재고는 변동될 수 있어요.</p>
`;
}

function ensureDir(d) {
  if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true });
}

function main() {
  if (!fs.existsSync(DATA)) {
    console.error(`[generate-pages] not found: ${DATA}`);
    process.exit(1);
  }
  let items;
  try {
    items = JSON.parse(fs.readFileSync(DATA, 'utf-8'));
  } catch (e) {
    console.error('[generate-pages] invalid JSON in data/products.json');
    console.error(e.message);
    process.exit(1);
  }
  if (!Array.isArray(items)) {
    console.error('[generate-pages] data must be an array');
    process.exit(1);
  }

  ensureDir(OUT_DIR);
  let changed = 0;

  for (const it of items) {
    const id = String(it.product_id || it.pageKey || it.id || '').trim();
    if (!id) continue;

    const content = frontMatter(it) + '\n' + body(it) + '\n';
    const outPath = path.join(OUT_DIR, `${id}.md`);
    const prev = fs.existsSync(outPath) ? fs.readFileSync(outPath, 'utf-8').trim() : '';
    if (prev !== content.trim()) {
      fs.writeFileSync(outPath, content, 'utf-8');
      changed++;
      console.log(`[generate-pages] wrote: p/${id}.md`);
    }
  }

  console.log(`[generate-pages] changed=${changed}`);
}

main();
