# ===== 0) Imports =====
import os
import sys
import time
import hmac
import hashlib
import base64  # 참고용(미사용), 유지해도 무방
import requests
import random
import pathlib
import urllib.parse
import json

# ===== 0.5) 내부 상세 URL 헬퍼 =====
def ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass

def get_detail_paths(item: dict) -> tuple[str, str]:
    """
    내부 상세 페이지의 (로컬 파일 경로, 퍼블릭 URL)을 돌려준다.
    기본 규칙: /p/{productId}.html
    productId가 없으면 productName 기반 해시로 대체.
    주의: SITE_URL은 파일 아래쪽에서 정의돼 있어도 문제 없음(함수 호출 시점에 참조됨).
    """
    pid = item.get("productId")
    if pid:
        pid = str(pid)
        local = os.path.join("p", f"{pid}.html")
        url   = f"{SITE_URL}p/{pid}.html"
        return local, url

    # fallback: productId가 없는 희귀 케이스
    name = (item.get("productName") or "item").strip()
    h = hashlib.md5(name.encode("utf-8")).hexdigest()[:10]
    local = os.path.join("p", f"{h}.html")
    url   = f"{SITE_URL}p/{h}.html"
    return local, url
    
def _fmt_price_safe(v):
    # 가격 콤마 포맷(네가 이미 _fmt_price가 있으면 그거 써도 됨)
    try:
        n = int(float(str(v).replace(",", "").strip()))
        return f"{n:,}"
    except:
        return str(v).strip()

def build_product_detail_html(item: dict, detail_url: str) -> str:
    name = (item.get("productName") or "").strip()
    price = _fmt_price_safe(item.get("productPrice") or item.get("price") or "")
    img = (item.get("imageUrl") or item.get("productImage") or item.get("image") or "").strip()
    coupang_url = (item.get("productUrl") or item.get("link") or "").strip()
    if img.startswith("//"):
        img = "https:" + img
    elif img.startswith("http:"):
        img = "https:" + img[5:]
    if not img:
        img = "https://via.placeholder.com/800x500?text=No+Image"

    # JSON-LD(Product)
    product_ld = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": name,
        "image": img,
        "offers": {
            "@type": "Offer",
            "priceCurrency": "KRW",
            "price": str(item.get("productPrice") or item.get("price") or ""),
            "url": coupang_url
        },
        "url": detail_url
    }
    ld_json = json.dumps(product_ld, ensure_ascii=False)

    title = f"{name} | YourShop"
    desc = f"{name} 베스트 가격/구성 살펴보고, 버튼으로 바로 확인해보세요."

    build_ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <!-- build:{build_ts} -->
  <meta charset="UTF-8">
  <title>{title}</title>
  <meta name="description" content="{desc}">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="canonical" href="{detail_url}">
  <meta name="referrer" content="no-referrer">

  <!-- Open Graph -->
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{desc}">
  <meta property="og:image" content="{img}">
  <meta property="og:url" content="{detail_url}">
  <meta name="twitter:card" content="summary_large_image">

  <script type="application/ld+json">
{ld_json}
  </script>

  <style>
    :root {{
      --text:#e5e7eb; --muted:#94a3b8; --card:#111827; --border:#1f2937; --accent:#22d3ee;
    }}
    body {{ background:#0b1020; color:var(--text); font-family:Arial,sans-serif; max-width:900px; margin:auto; padding:20px; }}
    h1 {{ margin:0 0 10px 0; }}
    .price {{ color:var(--accent); font-weight:800; margin:8px 0 14px 0; font-size:20px; }}
    img.hero {{ max-width:100%; border-radius:12px; display:block; }}
    .btn {{
      display:inline-block; margin-top:14px; padding:10px 14px; border-radius:12px;
      color:var(--text); text-decoration:none; border:1px solid #334155;
      background:linear-gradient(180deg,#0b1224 0%,#0a0f1f 100%); transition:.2s ease;
    }}
    .btn:hover {{ transform: translateY(-1px); border-color:#556; }}
    .notice {{ color:var(--muted); font-size:13px; margin:10px 0 20px 0; }}
    .section {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:14px; margin:16px 0; }}
  </style>
</head>
<body>
  <h1>{name}</h1>
  <p class="notice">※ 이 페이지의 외부 링크는 쿠팡 파트너스 링크이며, 일정액의 수수료를 받을 수 있습니다.</p>

  <div class="section">
    <img class="hero" src="{img}" alt="{name}" loading="lazy" referrerpolicy="no-referrer">
    <div class="price">{price}원</div>
    <a class="btn" href="{coupang_url}" target="_blank" rel="nofollow sponsored noopener">쿠팡에서 보기</a>
  </div>

  <div class="section">
    <h2 style="margin:0 0 8px 0;">상품 한눈 요약</h2>
    <ul style="margin:0; padding-left:18px; line-height:1.6;">
      <li>대표 이미지/가격은 파트너스 응답을 기준으로 표시됩니다.</li>
      <li>최신 가격/재고/혜택은 ‘쿠팡에서 보기’에서 다시 확인하세요.</li>
    </ul>
  </div>
</body>
</html>
"""
    return html
def write_product_detail_pages(items: list):
    """
    오늘 배치(items)에 대해 /p/{productId}.html 상세 페이지 파일 생성.
    """
    ensure_dir("p")
    written = 0
    for it in items:
        local, url = get_detail_paths(it)
        try:
            html = build_product_detail_html(it, url)
            with open(local, "w", encoding="utf-8") as f:
                f.write(html)
            written += 1
        except Exception as e:
            print("[WARN] detail write fail:", local, e)
    if DEBUG:
        print(f"[DETAIL] written={written}")
        
# ===== 1) 환경/설정 로드 =====
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
COUNT = int(os.getenv("COUNT", "30"))              # 노출 개수 (기본 30)
DEBUG = os.getenv("DEBUG_LOG", "0") == "1"         # 디버그 로그 on/off

DOMAIN = "https://api-gateway.coupang.com"
SITE_URL = "https://rkskqdl-a11y.github.io/yourshop/"

SEARCH_KEYWORDS = [
    "노트북", "게이밍 모니터", "무선 이어폰", "스마트워치", "청소기",
    "안마의자", "커피머신", "에어프라이어", "게이밍 키보드", "마우스",
    "아이폰 케이스", "갤럭시 충전기", "스탠드 조명", "공기청정기", "전동 킥보드",
    "자전거", "헬스 보충제", "캠핑 용품", "여행 가방", "패션 신발", "아동 장난감"
]


# ===== 2) 시작 로그(디버그) =====
def _mask(v):
    return "(none)" if not v else f"len={len(v)} head={v[:3]}***"

print("ACCESS_KEY_PRESENT=", "YES" if ACCESS_KEY else "NO", _mask(ACCESS_KEY))
print("SECRET_KEY_PRESENT=", "YES" if SECRET_KEY else "NO", _mask(SECRET_KEY))
print("== DEBUG START ==")
print("PYTHON_VERSION=", sys.version)
print("CWD=", os.getcwd())
print("FILES=", [p.name for p in pathlib.Path(".").glob("*")])
print("HAS_INDEX=", os.path.exists("index.html"))
print("DEBUG_LOG=", os.getenv("DEBUG_LOG", ""))
print("COUNT_ENV=", os.getenv("COUNT", ""))


# ===== 3) HMAC (쿠팡 문서 포맷: hexdigest + yyMMddTHHmmssZ) =====
def generate_hmac(method: str, path_with_query: str, secret_key: str, access_key: str, dt: str | None = None) -> tuple[str, str]:
    """
    쿠팡 문서 포맷:
    - signed-date: yyMMddTHHmmssZ (UTC)
    - signature: HMAC-SHA256 hexdigest 문자열 (base64 아님)
    - message = signed-date + METHOD + path + query
    반환: (Authorization 헤더, signed-date)
    """
    if dt is None:
        dt = time.strftime('%y%m%d', time.gmtime()) + 'T' + time.strftime('%H%M%S', time.gmtime()) + 'Z'

    path, query = (path_with_query.split("?", 1) + [""])[:2]
    message = dt + method + path + query

    signature = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    auth = f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={dt}, signature={signature}"
    return auth, dt


# ===== 4) 상품 조회(검색 API) =====
def fetch_products(keyword: str):
    """
    GET /v2/providers/affiliate_open_api/apis/openapi/v1/products/search
    - PreparedRequest로 최종 URL 생성 → 그 path+query로 서명
    - limit 20 시도 후 rCode 400(limit out of range)이면 10으로 재시도
    - 응답 JSON에서 리스트 추출 → 필드 정규화(productName/productPrice/imageUrl/productUrl) 후 반환
    """
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"

    def do_request(limit_val: int):
        params = {"keyword": keyword, "limit": limit_val}
        # 최종 URL 준비
        req = requests.Request("GET", DOMAIN + path, params=params)
        prep = req.prepare()
        parsed = urllib.parse.urlsplit(prep.url)
        path_with_query = parsed.path + (("?" + parsed.query) if parsed.query else "")
        # 서명(hexdigest + yyMMddTHHmmssZ)
        authorization, _ = generate_hmac("GET", path_with_query, SECRET_KEY, ACCESS_KEY, None)
        # 동일 prepared 요청에 헤더 주입
        prep.headers["Authorization"] = authorization
        prep.headers["Content-Type"] = "application/json;charset=UTF-8"
        s = requests.Session()
        resp = s.send(prep, timeout=10)
        if DEBUG:
            print(f"[REQ] url={resp.request.url} status={resp.status_code} len={len(resp.content)}")
            print("[BODYFULL]", (resp.text or "")[:2000])
        return resp

    # 1차: 20
    resp = do_request(20)
    try:
        j = resp.json()
    except Exception:
        j = {}

    # limit 에러 시 10으로 재시도
    if isinstance(j, dict) and (j.get("rCode") == "400" or j.get("code") == "ERROR") and "limit is out of range" in (str(j.get("rMessage","")) + str(j.get("message",""))):
        if DEBUG:
            print("[INFO] retry with smaller limit=10")
        resp = do_request(10)
        try:
            j = resp.json()
        except Exception:
            j = {}

    # HTTP 오류
    try:
        resp.raise_for_status()
    except Exception as e:
        print("[WARN] HTTP error:", e)
        return []

    # API 성공 코드 확인
    if isinstance(j, dict):
        rcode = j.get("rCode") or j.get("code")
        if rcode and str(rcode).upper() not in ("0", "SUCCESS"):
            print("[INFO] API not success:", rcode, j.get("rMessage") or j.get("message"))
            return []

    # data에서 후보 리스트 찾기
    data_node = j.get("data") if isinstance(j, dict) else None
    candidates = None

    if isinstance(data_node, list):
        candidates = data_node
    elif isinstance(data_node, dict):
        for k in ("productData", "products", "content", "productList", "items"):
            v = data_node.get(k)
            if isinstance(v, list) and v:
                candidates = v
                break

    if not candidates and isinstance(j, dict):
        for k in ("productData", "products", "content", "productList", "items"):
            v = j.get(k)
            if isinstance(v, list) and v:
                candidates = v
                break

    if not candidates:
        if DEBUG:
            if isinstance(data_node, dict):
                print("[INFO] no candidates; data keys:", list(data_node.keys()))
            else:
                print("[INFO] data is:", type(data_node).__name__)
        return []

    # 필드 정규화 (이미지: productImage도 커버)
    def norm(p: dict) -> dict:
        return {
            "productName":  p.get("productName") or p.get("title") or "",
            "productPrice": p.get("productPrice") or p.get("price") or p.get("lowestPrice") or "",
            "imageUrl":     (p.get("imageUrl") or p.get("productImage") or p.get("image") or ""),
            "productUrl":   p.get("productUrl") or p.get("link") or ""
        }

    items = [norm(x) for x in candidates if isinstance(x, dict)]
    if DEBUG:
        print("PARSED_COUNT=", len(items))
        if items:
            print("FIRST_ITEM_SAMPLE=", {k: items[0].get(k) for k in ("productName","productPrice","imageUrl","productUrl")})
    return items


# ===== 5) 여러 키워드 합쳐서 COUNT개 만들기 =====
def fetch_random_products():
    all_items = []
    for kw in SEARCH_KEYWORDS:
        try:
            items = fetch_products(kw)
            if items:
                all_items.extend(items)
        except Exception as e:
            if DEBUG:
                print("[WARN] fetch fail for", kw, e)
    # 섞고 COUNT개만 사용
    random.shuffle(all_items)
    return all_items[:COUNT]


# ===== 6) HTML 생성(이미지 보강 포함) =====
def build_html(products):
    seo_title = "오늘의 추천 특가상품 30선 | 쇼핑몰 베스트"
    seo_description = "가전제품, 패션, 캠핑용품, 헬스, 아동 장난감까지 오늘의 추천 베스트 특가상품 30개를 모았습니다."
    seo_keywords = ",".join(SEARCH_KEYWORDS)
    og_image = ""
    if products:
        og_image = (products[0].get("imageUrl")
                    or products[0].get("productImage")
                    or products[0].get("image")
                    or "")

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>{seo_title}</title>
    <meta name="description" content="{seo_description}">
    <meta name="keywords" content="{seo_keywords}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="referrer" content="no-referrer">

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
        article img {{ max-width: 100%; border-radius: 10px; display: block; }}
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
    # 카드 루프
    for p in products:
        name = (p.get("productName") or p.get("title") or "")[:60]
        desc = (p.get("productName") or p.get("title") or "")[:120]
        price = p.get("productPrice") or p.get("price") or ""

        # 이미지 우선순위 및 정리
        img = (p.get("imageUrl") or p.get("productImage") or p.get("image") or "").strip()
        link = (p.get("productUrl") or p.get("link") or "#").strip()

        # 스킴 보정: //, http → https
        if img.startswith("//"):
            img = "https:" + img
        elif img.startswith("http:"):
            img = "https:" + img[5:]

        # 빈 값이면 플레이스홀더
        if not img:
            img = "https://via.placeholder.com/600x400?text=No+Image"

        html += f"""
        <article itemscope itemtype="https://schema.org/Product">
            <h2 itemprop="name">{name}...</h2>
            <img src="{img}" alt="{name}" itemprop="image" loading="lazy" referrerpolicy="no-referrer">
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


# ===== 7) 사이트맵/로봇 =====
def build_sitemap(products):
    # 외부 도메인(쿠팡) 링크는 넣지 않는다. 내 사이트의 대표 URL만 등록.
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


# ===== 8) 메인 =====
if __name__ == "__main__":
    ensure_dir("p")
    products = fetch_random_products()
    # 상세 페이지 생성(오늘 30개)
    write_product_detail_pages(products)
    html = build_html(products)
    sitemap = build_sitemap(products)
    robots = build_robots()

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots)

    print("[OK] index.html/sitemap.xml/robots.txt written")
    print("== DEBUG END ==")
