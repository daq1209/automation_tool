import base64

# Đảm bảo file service_account.json đang nằm cùng thư mục
try:
    with open("service_account.json", "rb") as f:
        json_bytes = f.read()

    # Mã hóa sang Base64
    encoded_str = base64.b64encode(json_bytes).decode("utf-8")

    print("\n" + "="*50)
    print("COPY ĐOẠN MÃ DƯỚI ĐÂY VÀO FILE secrets.toml:")
    print("="*50 + "\n")
    print(encoded_str)
except FileNotFoundError:
    print("Lỗi: Không tìm thấy file 'service_account.json' để mã hóa!")