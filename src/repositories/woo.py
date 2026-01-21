import requests
import json
import time
from requests.auth import HTTPBasicAuth
from config import Config
from src.utils.logger import logger  

# --- [NEW] FAST SKU FETCHING ---
def get_all_skus_fast(domain, secret):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-all-skus"
    headers = {"x-secret": secret}
    
    for attempt in range(1, Config.MAX_RETRIES + 1):
        try:
            res = requests.get(url, headers=headers, timeout=60)
            if res.status_code == 200:
                return set(res.json().get('skus', []))
            if res.status_code in [500, 502, 503, 504, 429]:
                logger.warning(f"get_all_skus retry {attempt}/{Config.MAX_RETRIES} - Status: {res.status_code}")
                time.sleep(Config.RETRY_DELAY * attempt)
                continue
            return set()
        except requests.exceptions.Timeout as e:
            logger.error(f"get_all_skus timeout on attempt {attempt}: {e}")
            if attempt < Config.MAX_RETRIES:
                time.sleep(Config.RETRY_DELAY * attempt)
            else:
                return set()
        except requests.exceptions.ConnectionError as e:
            logger.error(f"get_all_skus connection error on attempt {attempt}: {e}")
            if attempt < Config.MAX_RETRIES:
                time.sleep(Config.RETRY_DELAY * attempt)
            else:
                return set()
        except Exception as e:
            logger.error(f"get_all_skus unexpected error: {e}", exc_info=True)
            return set()
    return set()

# --- V12 CORE APIs ---
def post_product_batch_v12(domain, secret, products_list):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/import-product-batch"
    headers = {"x-secret": secret, "Content-Type": "application/json"}
    payload = {"products": products_list}
    
    for attempt in range(1, Config.MAX_RETRIES + 1):
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=Config.API_TIMEOUT)
            if res.status_code == 200: return res
            if res.status_code in [500, 502, 503, 504, 429]:
                time.sleep(Config.RETRY_DELAY * attempt)
                continue
            return res 
        except requests.exceptions.RequestException as e:
            logger.warning(f"Post batch attempt {attempt} failed: {str(e)}")
            time.sleep(Config.RETRY_DELAY * attempt)
    return None

def trigger_process_media(domain, secret, limit=1):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/process-pending-media"
    headers = {"x-secret": secret}
    params = {"limit": limit}
    
    for attempt in range(1, Config.MAX_RETRIES + 1):
        try:
            res = requests.post(url, headers=headers, params=params, timeout=120)
            if res.status_code == 200:
                return res.json()
            if res.status_code in [500, 502, 503, 504, 429]:
                logger.warning(f"trigger_process_media retry {attempt}/{Config.MAX_RETRIES}")
                time.sleep(Config.RETRY_DELAY * attempt)
                continue
            return None
        except requests.exceptions.Timeout as e:
            logger.error(f"trigger_process_media timeout: {e}")
            if attempt < Config.MAX_RETRIES:
                time.sleep(Config.RETRY_DELAY * attempt)
            else:
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"trigger_process_media request error: {e}")
            if attempt < Config.MAX_RETRIES:
                time.sleep(Config.RETRY_DELAY * attempt)
            else:
                return None
        except Exception as e:
            logger.error(f"trigger_process_media unexpected error: {e}", exc_info=True)
            return None
    return None

# --- LEGACY APIs ---
def fetch_product_ids_page(domain, ck, cs, page=1, status='publish'):
    url = f"{domain.rstrip('/')}/wp-json/wc/v3/products"
    params = {"per_page": 100, "page": page, "fields": "id", "status": status}
    try:
        return requests.get(url, auth=HTTPBasicAuth(ck, cs), params=params, timeout=30)
    except requests.exceptions.RequestException as e:
        logger.error(f"fetch_product_ids_page failed (page {page}): {e}")
        return None

def fetch_product_list_custom(domain, secret, limit=50, search_term=None):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-product-list"
    headers = {"x-secret": secret}
    params = {"limit": limit}
    if search_term: params["search"] = search_term
    try:
        return requests.get(url, headers=headers, params=params, timeout=30).json()
    except requests.exceptions.RequestException as e:
        logger.error(f"fetch_product_list_custom failed: {e}")
        return []

def fetch_media_preview_custom(domain, secret, limit=50, search_term=None):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-media-list"
    headers = {"x-secret": secret}
    params = {"limit": limit}
    if search_term: params["search"] = search_term
    try:
        # Timeout 5 mins for large datasets (e.g. 10k images)
        return requests.get(url, headers=headers, params=params, timeout=300).json()
    except requests.exceptions.RequestException as e:
        logger.error(f"fetch_media_preview_custom failed: {e}")
        return []

def check_product_exists(domain, secret, sku):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/check-product"
    headers = {"x-secret": secret}
    try:
        res = requests.post(url, json={"sku": sku}, headers=headers, timeout=10)
        return res.json().get('status') == 'exists' if res.status_code == 200 else None
    except requests.exceptions.RequestException as e:
        logger.error(f"check_product_exists failed for SKU {sku}: {e}")
        return None

def delete_products_batch_custom(domain, secret, ids):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-product-batch"
    headers = {"x-secret": secret, "Content-Type": "application/json"}
    try:
        res = requests.post(url, json={"ids": ids}, headers=headers, timeout=60)
        if res.status_code == 200:
            data = res.json()
            return True, data.get('deleted_count', 0), data.get('deleted_items', [])
        return False, 0, []
    except requests.exceptions.RequestException as e:
        logger.error(f"delete_products_batch failed for {len(ids)} products: {e}")
        return False, 0, []

def delete_media_batch(domain, secret, ids):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/delete-media-batch"
    headers = {"x-secret": secret}
    try:
        res = requests.post(url, json={"ids": ids}, headers=headers, timeout=60)
        return res.status_code == 200
    except requests.exceptions.RequestException as e:
        logger.error(f"delete_media_batch failed for {len(ids)} items: {e}")
        return False

def get_all_media_ids(domain, secret):
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/get-all-media-ids"
    headers = {"x-secret": secret}
    try:
        res = requests.get(url, headers=headers, timeout=60)
        return res.json().get('ids', []) if res.status_code == 200 else []
    except requests.exceptions.RequestException as e:
        logger.error(f"get_all_media_ids failed: {e}")
        return []

def update_media_batch_custom(domain, secret, updates):
    """
    updates = [{'id': 123, 'title': 'New Name'}, ...]
    """
    url = f"{domain.rstrip('/')}/wp-json/test-secret/v1/update-media-batch"
    headers = {"x-secret": secret}
    try:
        res = requests.post(url, headers=headers, json={"updates": updates}, timeout=120)
        if res.status_code == 200:
            return res.json()
        return {"status": "error", "message": f"HTTP {res.status_code}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"update_media_batch_custom failed: {e}")
        return {"status": "error", "message": str(e)}