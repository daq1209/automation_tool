import streamlit as st

def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def get_val(row, keys_to_check):
    """Tìm giá trị trong row bất kể hoa thường"""
    row_lower = {k.lower().strip(): v for k, v in row.items()}
    for k in keys_to_check:
        key_lower = k.lower().strip()
        if key_lower in row_lower:
            val = str(row_lower[key_lower]).strip()
            if val and val.lower() != 'nan' and val.lower() != 'none': return val
    return ""