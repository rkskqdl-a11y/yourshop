import os
import sys
import time
import hmac
import hashlib
import base64
import requests
import random
import pathlib
import urllib.parse

# === 헬퍼: 인코딩 ===
def _enc_rfc3986(v: str) -> str:
    # 공백 → %20, 안전문자만 허용(RFC3986)
    return urllib.parse.quote(str(v), safe="-_.~")

def _build_query(params, space_plus=False) -> str:
    # space_plus=True → urllib 표준(+)
    # space_plus=False → RFC3986(%20)
    if space_plus:
        return urllib.parse.urlencode(params, doseq=True)
    return "&".join(f"{_enc_rfc3986(k)}={_enc_rfc3986(v)}" for k, v in params)
    
# 1) 환경변수(시크릿) 먼저 로드
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# 2) 마스킹 함수 + 키 존재/길이 로그
def _mask(v):
    return "(none)" if not v else f"len={len(v)} head={v[:3]}***"

print("ACCESS_KEY_PRESENT=", "YES" if ACCESS_KEY else "NO", _mask(ACCESS_KEY))
print("SECRET_KEY_PRESENT=", "YES" if SECRET_KEY else "NO", _mask(SECRET_KEY))
# ===== [디버그: 실행 환경 출력] =====
print("== DEBUG START ==")
print("PYTHON_VERSION=", sys.version)
print("CWD=", os.getcwd())
print("FILES=", [p.name for p in pathlib.Path(".").glob("*")])
print("HAS_INDEX=", os.path.exists("index.html"))
print("DEBUG_LOG=", os.getenv("DEBUG_LOG", ""))
print("COUNT_ENV=", os.getenv("COUNT", ""))

# ===== [환경변수/상수] =====
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
COUNT = int(os.getenv("COUNT", "30"))  # 하루에 몇 개 뿌릴지 컨트롤
DEBUG = os.getenv("DEBUG_LOG") == "1"

DOMAIN = "https://api-gateway.coupang.com"

# 대표 사이트 주소(정확한 도메인 + 끝에 / 권장)
SITE_URL = "https://rkskqdl-a11y.github.io/yourshop/"

SEARCH_KEYWORDS = [
    "노트북", "게이밍 모니터", "무선 이어폰", "스마트워치", "청소기",
    "안마의자", "커피머신", "에어프라이어", "게이밍 키보드", "마우스",
    "아이폰 케이스", "갤럭시 충전기", "스탠드 조명", "공기청정기", "전동 킥보드",
    "자전거", "헬스 보충제", "캠핑 용품", "여행 가방", "패션 신발", "아동 장난감"
]

# 이미 맨 위에 있음: import urllib.parse, import requests, import time, hmac, hashlib, base64

def generate_hmac(method: str, path_with_query: str, secret_key: str, access_key: str, dt: str) -> str:
    """
    dt: 날짜 문자열(이미 만들어진 값 사용)
    path_with_query: '/.../path?key=val&...' 최종 문자열(쿼리 포함)
    """
    path, query = (path_with_query.split("?", 1) + [""])[:2]
    message = dt + method + path + query
    signature = hmac.new(secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).digest()
    signed = base64.b64encode(signature).decode("utf-8")
    return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={dt}, signature={signed}"

# === 상품 조회(멀티 포맷 자동 시도) ===
def fetch_products(keyword: str):
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    params = [("keyword", keyword), ("limit", 50)]

    # 시도할 조합(상대가 뭘 기대하든 자동으로 맞추기)
    # 1) ISO8601 + RFC3986(%20)
    # 2) yyyymmddTHHMMSSZ + RFC3986(%20)
    # 3) yyyymmddTHHMMSSZ + urlencoded(+)
    attempts = [
        (lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), False),
        (lambda: time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), False),
        (lambda: time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()), True),
    ]

    last_err = None
    for dt_func, space_plus in attempts:
        dt = dt_func()
        q = _build_query(params, space_plus=space_plus)
        path_with_query = f"{path}?{q}"
        url = f"{DOMAIN}{path_with_query}"

        auth = generate_hmac("GET", path_with_query, SECRET_KEY, ACCESS_KEY, dt)
        headers = {
            "Authorization": auth,
            "Content-Type": "application/json;charset=UTF-8",
            "X-Authorization-Date": dt,  # 참고용
        }

        resp = requests.get(url, headers=headers, timeout=10)

        if 'DEBUG' in globals() and DEBUG:
            enc_mode = "plus" if space_plus else "rfc3986"
            print(f"[TRY] dt={dt} enc={enc_mode} url={resp.request.url} status={resp.status_code} len={len(resp.content)}")
            if resp.status_code >= 400:
                print("[BODY]", (resp.text or "")[:300])
            else:
                print("[OK] matched: dt=", dt, " enc=", enc_mode)

        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception as e:
                last_err = e
                break
            return data.get("data", {}).get("productData", []) or []
        else:
            last_err = resp.text

    print(f"[WARN] all signature attempts failed. last_err={str(last_err)[:200]}")
    return []

def fetch_random_products():
    all_products = []
    for kw in SEARCH_KEYWORDS:
        all_products.extend(fetch_products(kw))
    random.shuffle(all_products)
    # COUNT 개수만큼 자르기
    picked = all_products[:COUNT] if all_products else []
    return picked

def build_html(products):
    seo_title = "오늘의 추천 특가상품 30선 | 쇼핑몰 베스트"
    seo_description = "가전제품, 패션, 캠핑용품, 헬스, 아동 장난감까지 오늘의 추천 베스트 특가상품 30개를 모았습니다."
    seo_keywords = ",".join(SEARCH_KEYWORDS)
    og_image = (products[0].get("imageUrl") if products else "") or ""

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
    <meta property="og:image" content="{og_image}">
    <meta property="og:url" content="{SITE_URL}">
    <link rel="canonical" href="{SITE_URL}">
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
        name = (p.get("productName") or "")[:60]
        desc = (p.get("productName") or "")[:120]
        price = p.get("price") or ""
        img = p.get("imageUrl") or ""
        link = p.get("productUrl") or "#"
        html += f"""
        <article itemscope itemtype="https://schema.org/Product">
            <h2 itemprop="name">{name}...</h2>
            <img src="{img}" alt="{name}" itemprop="image">
            <p class="price"><span itemprop="price">{price}</span>원</p>
            <a class="btn" href="{link}" target="_blank" rel="nofollow noopener" itemprop="url">👉 보러가기</a>
            <meta itemprop="brand" content="쿠팡">
            <meta itemprop="description" content="{desc}">
        </article>
"""
    html += """
    </div>
</body>
</html>
"""
    return html

def build_sitemap(products):
    # 주의: 쿠팡 외부 URL은 네 도메인이 아니므로 sitemap에는 넣지 않는 게 정석
    # 네 사이트 대표 URL만 넣자.
    urls = [SITE_URL]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f"  <url><loc>{url}</loc></url>\n"
    xml += "</urlset>"
    return xml

def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}sitemap.xml
"""

if __name__ == "__main__":
    # 데이터 수집
    products = fetch_random_products()

    # 수집 결과 로그
    print(f"PRODUCT_COUNT={len(products)}")
    if products:
        try:
            print("FIRST_ITEM_TITLE=", str(products[0].get("productName", ""))[:80])
        except Exception as e:
            print("[WARN] first item preview failed:", e)

    # 디버그 모드에서 비었으면 더미 1개 주입(파이프라인 점검)
    if not products and DEBUG:
        products = [{
            "productName": "샘플 상품(점검용)",
            "price": "9,900",
            "imageUrl": "https://via.placeholder.com/600x400?text=Sample",
            "productUrl": "https://www.coupang.com/",
        }]
        print("[WARN] products empty → injected 1 dummy item for pipeline test.")

    # 파일 생성
    html = build_html(products)
    sitemap = build_sitemap(products)
    robots = build_robots()

    # 저장
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots)

    print("[OK] index.html/sitemap.xml/robots.txt written")
    print("== DEBUG END ==")
