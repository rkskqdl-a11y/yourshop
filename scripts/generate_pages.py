# scripts/generate_pages.py
import os, sys, json, re, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P_DIR = ROOT / "p"

FRONT_TEMPLATE = """---
layout: product
title: "{title}"
product_id: {product_id}
image_url: "{image_url}"
description: "{description}"
brand: "{brand}"
price_number: "{price_number}"
{rating_block}---
"""

BODY_TEMPLATE = """<!-- 본문(자동 생성, 원하면 수정) -->
<h2>요약</h2>
<p>{description}</p>

<ul>
  <li>브랜드: {brand}</li>
  <li>상품번호: {product_id}</li>
  <li>가격: {price_number}원</li>
</ul>

<p>가격·재고는 변동될 수 있어요.</p>
"""

def sanitize_text(s):
    if s is None: return ""
    s = str(s).strip()
    s = s.replace('"', '\\"')
    s = re.sub(r'\s+', ' ', s)
    return s

def digits_only_price(s):
    if s is None: return ""
    return re.sub(r'[^0-9]', '', str(s))

def build_front_matter(item):
    title = sanitize_text(item.get("title", "상품"))
    product_id = str(item.get("product_id") or item.get("pageKey") or item.get("id") or "").strip()
    image_url = sanitize_text(item.get("image_url", ""))
    description = sanitize_text(item.get("description", ""))
    brand = sanitize_text(item.get("brand", "쿠팡"))
    price_number = digits_only_price(item.get("price") or item.get("price_number") or "")

    rating_value = str(item.get("rating_value") or "").strip()
    review_count = str(item.get("review_count") or "").strip()
    rating_block = ""
    if rating_value and review_count:
        rating_block = f'rating_value: "{rating_value}"\nreview_count: "{review_count}"\n'
    # 들여쓰기, 줄바꿈 주의
    fm = FRONT_TEMPLATE.format(
        title=title,
        product_id=product_id,
        image_url=image_url,
        description=description,
        brand=brand,
        price_number=price_number,
        rating_block=rating_block
    )
    return fm, {
        "title": title,
        "product_id": product_id,
        "image_url": image_url,
        "description": description,
        "brand": brand,
        "price_number": price_number
    }

def build_body(ctx):
    return BODY_TEMPLATE.format(**ctx)

def write_page(item):
    P_DIR.mkdir(parents=True, exist_ok=True)
    product_id = str(item.get("product_id") or item.get("pageKey") or item.get("id") or "").strip()
    if not product_id:
        return False, "no_product_id"
    fm, ctx = build_front_matter(item)
    body = build_body(ctx)
    content = fm + "\n" + body + "\n"
    out = P_DIR / f"{product_id}.md"
    old = out.read_text(encoding="utf-8") if out.exists() else ""
    if old.strip() == content.strip():
        return False, "no_change"
    out.write_text(content, encoding="utf-8")
    return True, str(out)

def load_products(input_path):
    # 입력은 JSON 배열 파일 가정. 필요하면 CSV/API로 확장 가능.
    p = Path(input_path)
    if not p.exists():
        raise FileNotFoundError(f"input not found: {input_path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        raise ValueError("input must be a list of products")
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_pages.py data/products.json")
        sys.exit(1)
    items = load_products(sys.argv[1])
    created, changed = 0, 0
    for it in items:
        ok, msg = write_page(it)
        if ok:
            if msg.endswith(".md"):
                if Path(msg).exists():
                    if "created" in msg: created += 1
            changed += 1
    print(f"[generate_pages] done. changed={changed}")

if __name__ == "__main__":
    main()
