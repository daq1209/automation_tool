import requests
import json
import time
from requests.auth import HTTPBasicAuth

# --- CONFIGURATION ---
MAX_RETRIES = 5  
RETRY_DELAY = 2  

# --- [NEW] FAST SKU FETCHING ---
def get_all_skus_fast(domain, secret):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-all-skus"
    headers = {"x-secret": secret}
    try:
        # Long timeout for DB query
        res = requests.get(url, headers=headers, timeout=60)
        if res.status_code == 200:
            # Return a Set for O(1) complexity
            return set(res.json().get('skus', []))
        return set()
    except:
        return set()

# --- V12 CORE APIs ---
def post_product_batch_v12(domain, secret, products_list):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/import-product-batch"
    headers = {"x-secret": secret, "Content-Type": "application/json"}
    payload = {"products": products_list}
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=60)
            if res.status_code == 200: return res
            if res.status_code in [500, 502, 503, 504, 429]:
                time.sleep(RETRY_DELAY * attempt)
                continue
            return res 
        except requests.exceptions.RequestException:
            time.sleep(RETRY_DELAY * attempt)
    return None

def trigger_process_media(domain, secret, limit=1):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/process-pending-media"
    headers = {"x-secret": secret}
    params = {"limit": limit}
    try:
        res = requests.post(url, headers=headers, params=params, timeout=120)
        return res.json() if res.status_code == 200 else None
    except: return None

# --- LEGACY APIs ---
def fetch_product_ids_page(domain, ck, cs, page=1, status='publish'):
    url = f"{domain.rstrip('/')}/wp-json/wc/v3/products"
    params = {"per_page": 100, "page": page, "fields": "id", "status": status}
    try: return requests.get(url, auth=HTTPBasicAuth(ck, cs), params=params, timeout=30)
    except: return None

def fetch_product_list_custom(domain, secret, limit=50, search_term=None):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-product-list"
    headers = {"x-secret": secret}
    params = {"limit": limit}
    if search_term: params["search"] = search_term
    try: return requests.get(url, headers=headers, params=params, timeout=30).json()
    except: return []

def fetch_media_preview_custom(domain, secret, limit=50, search_term=None):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-media-list"
    headers = {"x-secret": secret}
    params = {"limit": limit}
    if search_term: params["search"] = search_term
    try: return requests.get(url, headers=headers, params=params, timeout=30).json()
    except: return []

def check_product_exists(domain, secret, sku):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/check-product"
    headers = {"x-secret": secret}
    try:
        res = requests.post(url, json={"sku": sku}, headers=headers, timeout=10)
        return res.json().get('status') == 'exists' if res.status_code == 200 else None
    except: return None

def delete_products_batch_custom(domain, secret, ids):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-product-batch"
    headers = {"x-secret": secret, "Content-Type": "application/json"}
    try:
        res = requests.post(url, json={"ids": ids}, headers=headers, timeout=60)
        if res.status_code == 200:
            data = res.json()
            return True, data.get('deleted_count', 0), data.get('deleted_items', [])
        return False, 0, []
    except: return False, 0, []

def delete_media_batch(domain, secret, ids):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-media-batch"
    headers = {"x-secret": secret}
    try:
        res = requests.post(url, json={"ids": ids}, headers=headers, timeout=60)
        return res.status_code == 200
    except: return False

def get_all_media_ids(domain, secret):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-all-media-ids"
    headers = {"x-secret": secret}
    try:
        res = requests.get(url, headers=headers, timeout=60)
        return res.json().get('ids', []) if res.status_code == 200 else []
    except: return []