import requests
import json
from requests.auth import HTTPBasicAuth

def fetch_product_ids_page(domain, ck, cs, page=1, status='publish'):
    url = f"{domain.rstrip('/')}/wp-json/wc/v3/products"
    params = {"per_page": 100, "page": page, "fields": "id", "status": status}
    try: return requests.get(url, auth=HTTPBasicAuth(ck, cs), params=params, timeout=30)
    except: return None

def fetch_products_preview(domain, ck, cs, limit=50, status='publish', include_ids=None):
    url = f"{domain.rstrip('/')}/wp-json/wc/v3/products"
    params = { "per_page": limit, "page": 1, "status": status, "_fields": "id,name,sku,status,images" }
    if include_ids: params["include"] = ",".join(map(str, include_ids))
    try:
        res = requests.get(url, auth=HTTPBasicAuth(ck, cs), params=params, timeout=30)
        return res.json() if res.status_code == 200 else []
    except: return []

# [NEW] Fetch Media using Secret Key (Bypass WP Auth)
def fetch_media_preview_custom(domain, secret, limit=50, include_ids=None):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-media-list"
    headers = {"x-secret": secret}
    params = {"limit": limit}
    if include_ids: params["include"] = ",".join(map(str, include_ids))
    try:
        res = requests.get(url, headers=headers, params=params, timeout=30)
        return res.json() if res.status_code == 200 else []
    except: return []

def post_product_data(domain, secret, payload):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/import-product"
    headers = {"x-secret": secret, "Content-Type": "application/json"}
    try: return requests.post(url, json=payload, headers=headers, timeout=30)
    except: return None

def post_product_image(domain, secret, payload):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/import-image"
    headers = {"x-secret": secret, "Content-Type": "application/json"}
    try: return requests.post(url, json=payload, headers=headers, timeout=300)
    except: return None

def check_product_exists(domain, secret, sku):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/check-product"
    headers = {"x-secret": secret}
    try:
        res = requests.post(url, json={"sku": sku}, headers=headers, timeout=10)
        return res.json().get('status') == 'exists' if res.status_code == 200 else None
    except: return None

def get_all_media_ids(domain, secret):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-all-media-ids"
    headers = {"x-secret": secret}
    try:
        res = requests.get(url, headers=headers, timeout=60)
        return res.json().get('ids', []) if res.status_code == 200 else []
    except: return []

def delete_media_batch(domain, secret, ids):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-media-batch"
    headers = {"x-secret": secret}
    try:
        res = requests.post(url, json={"ids": ids}, headers=headers, timeout=60)
        return res.status_code == 200
    except: return False

def delete_media_by_date_range(domain, secret, start_date, end_date):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-media-date"
    headers = {"x-secret": secret}
    payload = {"start_date": str(start_date), "end_date": str(end_date)}
    try: return requests.post(url, json=payload, headers=headers, timeout=120)
    except: return None

def delete_products_batch_custom(domain, secret, ids):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-product-batch"
    headers = {"x-secret": secret, "Content-Type": "application/json"}
    payload = {"ids": ids}
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        if res.status_code == 200:
            data = res.json()
            return True, data.get('deleted_count', 0), data.get('deleted_items', [])
        return False, 0, []
    except: return False, 0, []