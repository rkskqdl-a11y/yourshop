import os
import time
import hmac
import hashlib
import base64
import requests
import random

# ✅ GitHub Secrets에서 API 키 불러오기
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

DOMAIN = "https://api-gateway.coupang.com"

# 🔽 검색할 키워드 (SEO에도 반영됨)
SEARCH_KEYWORDS = [
    "노트북", "게이밍 모니터", "무선 이어폰", "스마트워치", "청소기",
    "안마의자", "커피머신", "에어프라이어", "게이밍 키보드", "마우스",
    "아이폰 케이스", "갤럭시 충전기", "스탠드 조명", "공기청정기", "전동 킥보드",
    "자전거", "헬스 보충제", "캠핑 용품", "여행 가방", "패션 신발", "아동 장난감"
]

# ⚠️ 아래 주소에서 <> 안을 반드시 수정하세요!
# <내아이디> → 내 GitHub 아이디
# <내쇼핑몰주소> → 내가 원하는 주소 이름 (예: shop, store, best-deals)
SITE_URL = "https://rkskqdl.github.io/yourshop"

def generate_hmac(method, url, secret_key, access_key):
    path, query = (url.split("?", 1) + [""])[:2]
    datetime = time.strftime("%y%m%dT%H%M%S", time.gmtime())
    message = datetime + method + path + query
    signature = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    signed = base64.b64encode(signature).decode("utf-8")
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={datetime}, signature={signed}"

def fetch_products(keyword):
    url = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/search?keyword={keyword}&limit=50"
    authorization = generate_hmac("GET", url, SECRET_KEY, ACCESS_KEY)
    response = requests.get(DOMAIN + url, headers={"Authorization": authorization})
    data = response.json()
    return data.get("data", {}).get("productData", [])

def fetch_random_products():
    all_products = []
    for keyword in SEARCH_KEYWORDS:
        all_products.extend(fetch_products(keyword))
    return random.sample(all_products, min(30, len(all_products)))

def build_html(products):
    seo_title = "오늘의 추천 특가상품 30선 | 쇼핑몰 베스트"
    seo_description = "가전제품, 패션, 캠핑용품, 헬스, 아동 장난감까지 오늘의 추천 베스트 특가상품 30개를 모았습니다."
    seo_keywords = ",".join(SEARCH_KEYWORDS)

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{seo_title}</title>
    <meta name="description" content="{seo_description}">
    <meta name="keywords" content="{seo_keywords}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- Open Graph -->
    <meta property="og:title" content="{seo_title}">
    <meta property="og:description" content="{seo_description}">
    <meta property="og:image" content="{products[0].get("imageUrl") if products else ''}">
    <meta property="og:url" content="{SITE_URL}">
    <meta name="twitter:card" content="summary_large_image">

    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: auto; padding: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }}
        article {{ border: 1px solid #ddd; padding: 10px; border-radius: 10px; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); }}
        article img {{ max-width: 100%; border-radius: 10px; }}
        .price {{ font-weight: bold; color: red; margin-top: 5px; }}
        .btn {{ display: inline-block; margin-top: 10px; padding: 8px 12px; background: #ff5722; color: #fff; text-decoration: none; border-radius: 5px; }}
        .btn:hover {{ background: #e64a19; }}
    </style>
</head>
<body>
    <h1>{seo_title}</h1>
    <p>※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 일정액의 수수료를 제공받을 수 있습니다.</p>
    <div class="grid">
"""
    for p in products:
        html += f"""
        <article itemscope itemtype="https://schema.org/Product">
            <h2 itemprop="name">{p.get("productName")[:60]}...</h2>
            <img src="{p.get("imageUrl")}" alt="{p.get("productName")}" itemprop="image">
            <p class="price"><span itemprop="price">{p.get("price")}</span>원</p>
            <a class="btn" href="{p.get("productUrl")}" target="_blank" rel="nofollow" itemprop="url">👉 보러가기</a>
            <meta itemprop="brand" content="쿠팡">
            <meta itemprop="description" content="{p.get("productName")[:120]}">
        </article>
"""
    html += """
    </div>
</body>
</html>
"""
    return html

def build_sitemap(products):
    urls = [SITE_URL] + [p.get("productUrl") for p in products]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <url><loc>{url}</loc></url>\n"
    xml += "</urlset>"
    return xml

def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}/sitemap.xml
"""

if __name__ == "__main__":
    products = fetch_random_products()
    html = build_html(products)
    sitemap = build_sitemap(products)
    robots = build_robots()

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots)
