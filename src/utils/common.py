import streamlit as st

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def get_val(row, keys_to_check):
    row_lower = {k.lower().strip(): v for k, v in row.items()}
    for k in keys_to_check:
        key_lower = k.lower().strip()
        if key_lower in row_lower:
            val = str(row_lower[key_lower]).strip()
            if val and val.lower() != 'nan' and val.lower() != 'none': return val
    return ""

def col_idx_to_letter(n):
    string = ""
    while n >= 0:
        string = chr((n % 26) + 65) + string
        n = (n // 26) - 1
    return string

# --- GIAO DIỆN KHÓA: CUỘN ĐƯỢC - KHÔNG BẤM ĐƯỢC ---
def render_lock_screen():
    """
    Inject CSS để vô hiệu hóa nút bấm và input,
    nhưng VẪN CHO PHÉP cuộn chuột để xem log.
    """
    lock_html = """
    <style>
        /* 1. Vô hiệu hóa các thành phần tương tác cụ thể */
        button, 
        input, 
        textarea, 
        div[data-baseweb="select"], 
        div[role="radiogroup"], 
        div[data-testid="stCheckbox"],
        div[data-testid="stExpander"] {
            pointer-events: none !important; /* Không nhận click */
            opacity: 0.6 !important;         /* Làm mờ đi để biết là đang khóa */
            filter: grayscale(100%);         /* Chuyển sang trắng đen cho rõ */
            cursor: not-allowed !important;
        }

        /* 2. Đảm bảo trang web vẫn cuộn được */
        .stApp {
            pointer-events: auto !important;
            user-select: auto !important; /* Vẫn cho bôi đen copy text log */
            overflow: auto !important;
        }
        
        /* 3. Ẩn nút X tắt Sidebar để tránh user nghịch */
        button[kind="header"] {
            display: none !important;
        }
    </style>

    <script>
    // Vẫn giữ JS chặn tắt Tab cho an toàn
    window.onbeforeunload = function() {
        return "Data is processing. Do not close.";
    };
    </script>
    """
    return st.markdown(lock_html, unsafe_allow_html=True)

def remove_lock_screen():
    unlock_html = """
    <style>
        /* Khôi phục lại trạng thái bình thường */
        button, input, textarea, div[data-baseweb="select"], div[role="radiogroup"], div[data-testid="stCheckbox"] {
            pointer-events: auto !important;
            opacity: 1 !important;
            filter: none !important;
            cursor: pointer !important;
        }
        button[kind="header"] { display: block !important; }
    </style>
    <script>
        window.onbeforeunload = null;
    </script>
    """
    st.markdown(unlock_html, unsafe_allow_html=True)