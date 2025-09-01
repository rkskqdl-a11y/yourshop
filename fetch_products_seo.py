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
    productId가 없으면 (상품명|쿠팡링크) 해시로 대체.
    """
    pid = item.get("productId")
    if pid:
        pid = str(pid)
        local = os.path.join("p", f"{pid}.html")
        url   = f"{SITE_URL}p/{pid}.html"
        return local, url

    name = (item.get("productName") or "item").strip()
    out  = (item.get("productUrl") or item.get("link") or "").strip()
    key  = (name + "|" + out).encode("utf-8")
    h    = hashlib.md5(key).hexdigest()[:10]
    local = os.path.join("p", f"{h}.html")
    url   = f"{SITE_URL}p/{h}.html"
    return local, url

def _fmt_price_safe(v):
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
    <a class="btn" href="{coupang_url}" target="_blank" rel="nofollow sponsored noopener">실시간 가격보기</a>
  </div>

  <div class="section">
    <h2 style="margin:0 0 8px 0;">상품 한눈 요약</h2>
    <ul style="margin:0; padding-left:18px; line-height:1.6;">
      <li>이미지·가격은 검증된 응답 정보를 바탕으로 표기돼요(시점별 상이할 수 있어요).</li>
      <li>최신 가격/재고/혜택은 ‘실시간 가격보기’에서 다시 확인하세요.</li>
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

# 전 카테고리 랜덤용 큰 키워드 풀(전자 편향 해소)
BIG_CATEGORY_POOL = [
  # 식품/냉동/HMR
  "냉동식품", "만두", "피자", "떡갈비", "치킨너겟", "볶음밥", "즉석국", "즉석카레", "라면", "파스타 소스",
  "생수", "탄산음료", "커피 캡슐", "원두 커피", "차 티백", "에너지 드링크", "요거트", "시리얼", "과자", "초콜릿",
  # 생활/주방/세제
  "키친타월", "휴지", "세탁세제", "섬유유연제", "주방세제", "랩 호일 지퍼백", "밀폐용기", "프라이팬", "냄비", "도마 칼",
  "그릇 식기", "수납정리", "행거", "청소도구", "걸레 밀대", "빗자루 쓰레받기", "휴지통", "욕실용품", "샤워기", "수건",
  # 뷰티/헬스
  "스킨케어", "선크림", "클렌징폼", "바디로션", "샴푸", "트리트먼트", "헤어에센스", "향수", "마스크팩",
  "영양제", "비타민", "프로틴", "유산균", "눈건강", "오메가3", "헬스보충제", "의약외품", "마스크 KF94",
  # 패션/잡화
  "남성 반팔티", "여성 원피스", "후드티", "맨투맨", "청바지", "슬랙스", "러닝화", "샌들", "구두", "백팩",
  "크로스백", "지갑", "벨트", "모자 볼캡", "양말", "레깅스", "운동복", "언더웨어",
  # 유아/키즈/장난감
  "기저귀", "물티슈", "분유", "빨대컵", "아기식판", "유아샴푸", "유아세제",
  "레고", "퍼즐", "보드게임", "캐릭터 인형", "물놀이 장난감", "RC카",
  # 반려동물
  "강아지 사료", "고양이 사료", "고양이 모래", "간식 트릿", "리드줄 하네스", "장난감 낚싯대", "펫 방석 하우스",
  # 취미/스포츠/레저
  "자전거", "헬멧", "축구공", "농구공", "요가매트", "러닝머신", "덤벨", "캠핑 의자", "캠핑 테이블", "코펠",
  "랜턴", "버너", "아이스박스", "등산 스틱", "낚시 릴", "텐트",
  # 차량/공구
  "차량용 방향제", "거치대", "세차용품", "엔진오일", "타이어 공기압 측정기", "멀티탭", "드라이버 세트", "전동드릴",
  # 문구/도서/사무
  "볼펜", "형광펜", "노트", "파일 바인더", "라벨프린터", "A4용지", "스테이플러",
  # 가전은 최소만 섞기(편향 방지)
  "전기포트", "토스터기", "선풍기", "가습기", "헤어드라이어"
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
    - signed-date: yyMMddTHHmmssZ (UTC)
    - signature: HMAC-SHA256 hexdigest
    - message = signed-date + METHOD + path + query
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
    /v2/.../products/search
    - PreparedRequest 최종 URL → 그 path+query로 서명
    - limit 20 시도, rCode 400이면 10 재시도
    - 리스트 추출 → 정규화(내부 상세 경로 포함)
    """
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"

    def do_request(limit_val: int):
        params = {"keyword": keyword, "limit": limit_val}
        req = requests.Request("GET", DOMAIN + path, params=params)
        prep = req.prepare()
        parsed = urllib.parse.urlsplit(prep.url)
        path_with_query = parsed.path + (("?" + parsed.query) if parsed.query else "")

        authorization, _ = generate_hmac("GET", path_with_query, SECRET_KEY, ACCESS_KEY, None)
        prep.headers["Authorization"] = authorization
        prep.headers["Content-Type"] = "application/json;charset=UTF-8"

        s = requests.Session()
        resp = s.send(prep, timeout=10)
        if DEBUG:
            print(f"[REQ] url={resp.request.url} status={resp.status_code} len={len(resp.content)}")
            print("[BODYFULL]", (resp.text or "")[:2000])
        return resp

    resp = do_request(20)
    try:
        j = resp.json()
    except Exception:
        j = {}

    if isinstance(j, dict) and (j.get("rCode") == "400" or j.get("code") == "ERROR") and "limit is out of range" in (str(j.get("rMessage","")) + str(j.get("message",""))):
        if DEBUG:
            print("[INFO] retry with smaller limit=10")
        resp = do_request(10)
        try:
            j = resp.json()
        except Exception:
            j = {}

    try:
        resp.raise_for_status()
    except Exception as e:
        print("[WARN] HTTP error:", e)
        return []

    if isinstance(j, dict):
        rcode = j.get("rCode") or j.get("code")
        if rcode and str(rcode).upper() not in ("0", "SUCCESS"):
            print("[INFO] API not success:", rcode, j.get("rMessage") or j.get("message"))
            return []

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

    def norm(p: dict) -> dict:
        product_id = p.get("productId")
        internal_path = f"p/{product_id}.html" if product_id else None
        internal_url  = f"{SITE_URL}p/{product_id}.html" if product_id else None
        category = p.get("categoryName") or p.get("category") or ""
        return {
            "productName":  p.get("productName") or p.get("title") or "",
            "productPrice": p.get("productPrice") or p.get("price") or p.get("lowestPrice") or "",
            "imageUrl":     (p.get("imageUrl") or p.get("productImage") or p.get("image") or ""),
            "productUrl":   p.get("productUrl") or p.get("link") or "",
            "productId":    product_id,
            "rank":         p.get("rank"),
            "category":     category,
            "internalPath": internal_path,
            "internalUrl":  internal_url,
        }

    items = [norm(x) for x in candidates if isinstance(x, dict)]
    if DEBUG:
        print("PARSED_COUNT=", len(items))
        if items:
            print("FIRST_ITEM_SAMPLE=", {k: items[0].get(k) for k in ("productName","productPrice","imageUrl","productUrl","productId","internalPath","internalUrl")})
            lp, lu = get_detail_paths(items[0])
            print("DETAIL_SAMPLE_PATH_URL=", lp, lu)
    return items

# ===== 5) 여러 키워드 합쳐 COUNT개 =====
def fetch_random_products():
    all_items = []
    # 키워드별 10개씩 최대한 모아서 COUNT로 슬라이스
    for kw in SEARCH_KEYWORDS:
        try:
            items = fetch_products(kw)
            if items:
                all_items.extend(items)
        except Exception as e:
            if DEBUG:
                print("[WARN] fetch fail for", kw, e)
        if len(all_items) >= COUNT * 2:
            break
    random.shuffle(all_items)
    return all_items[:COUNT]

# ===== 6) HTML 생성(홈: 제목/이미지=내부, 버튼=쿠팡) =====
def build_html(products):
    seo_title = "오늘의 셀렉션 30 | YourShop"
    seo_description = "에디터가 엄선한 오늘의 셀렉션 30. 프리미엄 큐레이션으로 합리적인 쇼핑을 도와드립니다."
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
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: auto; padding: 20px; background:#0b1020; color:#e5e7eb; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; }}
        article {{ background:#111827; border:1px solid #1f2937; padding: 12px; border-radius: 12px; box-shadow: 0 6px 18px rgba(0,0,0,0.25); }}
        article img {{ max-width: 100%; border-radius: 10px; display: block; }}
        .price {{ font-weight: bold; color: #22d3ee; margin-top: 6px; }}
        .btn {{
          display:inline-block; margin-top:10px; padding:10px 14px; border-radius:12px;
          color:#e5e7eb; text-decoration:none; border:1px solid #334155;
          background: linear-gradient(180deg,#0b1224 0%, #0a0f1f 100%);
          transition: all .2s ease;
        }}
        .btn:hover {{ transform: translateY(-1px); border-color:#556; }}
        .title {{ display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; line-height:1.35; margin:0 0 8px 0; }}
        .title-link {{ text-decoration:none; color:inherit; }}
        .notice {{ color:#94a3b8; font-size:13px; margin-bottom: 12px; }}
    </style>
</head>
<body>
    <h1>{seo_title}</h1>
    <p class="notice">※ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 일정액의 수수료를 제공받을 수 있습니다.</p>
    <div class="grid">
"""
    for p in products:
        name_raw = p.get("productName") or p.get("title") or ""
        name = (name_raw or "")[:60]
        price_raw = p.get("productPrice") or p.get("price") or ""
        price = _fmt_price_safe(price_raw)
        img = (p.get("imageUrl") or p.get("productImage") or p.get("image") or "").strip()
        link_out = (p.get("productUrl") or p.get("link") or "#").strip()

        detail_path = p.get("internalPath")
        if not detail_path:
            detail_path, _ = get_detail_paths(p)

        if img.startswith("//"):
            img = "https:" + img
        elif img.startswith("http:"):
            img = "https:" + img[5:]
        if not img:
            img = "https://via.placeholder.com/600x400?text=No+Image"

        html += f"""
        <article itemscope itemtype="https://schema.org/Product">
          <a href="{detail_path}" class="title-link" itemprop="url">
            <h2 class="title" itemprop="name">{name}</h2>
          </a>
          <a href="{detail_path}">
            <img src="{img}" alt="{name}" itemprop="image" loading="lazy" referrerpolicy="no-referrer">
          </a>

          <p class="price"><span itemprop="price">{price}</span>원</p>

          <a class="btn" href="{link_out}" target="_blank" rel="nofollow sponsored noopener">
            실시간 가격보기
          </a>

          <meta itemprop="brand" content="쿠팡">
          <meta itemprop="description" content="{name}">
        </article>
        """

    html += """
    </div>
</body>
</html>
"""
    return html

# ===== 7) Sitemap / Robots =====
def build_sitemap(products):
    urls = [SITE_URL]  # 홈

    # /p 상세 페이지들 포함(인덱싱 가속)
    if os.path.isdir("p"):
        for name in os.listdir("p"):
            if name.endswith(".html"):
                urls.append(f"{SITE_URL}p/{name}")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    for url in urls:
        xml += f"  <url><loc>{url}</loc><lastmod>{now}</lastmod></url>\n"
    xml += "</urlset>"
    return xml

def build_robots():
    return f"""User-agent: *
Allow: /
Sitemap: {SITE_URL}sitemap.xml
"""

# ===== 8) 메인 =====
if __name__ == "__main__":
    ensure_dir("p")  # 상세 폴더 선생성
    products = fetch_random_products()
    write_product_detail_pages(products)  # /p/*.html 생성

    html = build_html(products)
    sitemap = build_sitemap(products)
    robots = build_robots()

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap)
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(robots)

    # 항상 변경을 만들어 커밋 보장
    build_ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    with open(".last_run", "w", encoding="utf-8") as f:
        f.write(build_ts)

    print("[OK] index.html/sitemap.xml/robots.txt written")
    print("== DEBUG END ==")
