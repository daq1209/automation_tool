import requests
from requests.auth import HTTPBasicAuth

# --- CÁC HÀM GỌI API WOOCOMMERCE ---

def post_product_data(domain, secret, payload):
    """Gọi API custom để import text"""
    api_url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/import-product"
    headers = {"x-secret": secret, "User-Agent": "Mozilla/5.0"}
    try:
        res = requests.post(api_url, json=payload, headers=headers, timeout=10)
        return res
    except Exception as e:
        return None

def post_product_image(domain, secret, payload):
    """
    Gọi API custom để import ảnh (Hỗ trợ Gallery)
    Payload nhận vào: { "sku": "...", "images": ["url1", "url2", ...] }
    """
    api_url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/import-image"
    headers = {"x-secret": secret, "User-Agent": "Mozilla/5.0"}
    try:
        # Tăng timeout lên 120s vì server phải tải nhiều ảnh
        res = requests.post(api_url, json=payload, headers=headers, timeout=120)
        return res
    except Exception as e:
        return None

def get_all_media_ids(domain, secret):
    """Lấy toàn bộ ID ảnh"""
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-all-media-ids"
    headers = {"x-secret": secret, "User-Agent": "Mozilla/5.0"}
    try:
        res = requests.get(url, headers=headers, timeout=30)
        if res.status_code == 200:
            return res.json().get('ids', [])
    except: pass
    return []

def delete_media_batch(domain, secret, ids):
    """Xóa 1 gói ảnh"""
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-media-batch"
    headers = {"x-secret": secret, "User-Agent": "Mozilla/5.0"}
    try:
        res = requests.post(url, json={"ids": ids}, headers=headers, timeout=60)
        return res.status_code == 200
    except: return False

def delete_media_by_date_range(domain, secret, start, end):
    """Xóa ảnh theo ngày"""
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-media-date"
    headers = {"x-secret": secret, "User-Agent": "Mozilla/5.0"}
    payload = { "start_date": str(start), "end_date": str(end) }
    try:
        return requests.post(url, json=payload, headers=headers, timeout=120)
    except Exception as e: return None

def fetch_product_ids_page(domain, ck, cs, page):
    """Lấy ID sản phẩm của 1 trang (API chuẩn WC)"""
    url = f"{domain.rstrip('/')}/wp-json/wc/v3/products"
    auth = HTTPBasicAuth(ck, cs)
    try:
        res = requests.get(url, auth=auth, params={"per_page": 100, "page": page, "status": "publish", "fields": "id"}, timeout=30)
        return res
    except: return None

def delete_products_batch(domain, ck, cs, ids):
    """Xóa 1 gói sản phẩm (API chuẩn WC)"""
    url = f"{domain.rstrip('/')}/wp-json/wc/v3/products/batch"
    auth = HTTPBasicAuth(ck, cs)
    try:
        res = requests.post(url, auth=auth, json={"delete": ids}, timeout=60)
        return res.status_code == 200, len(ids)
    except: return False, 0