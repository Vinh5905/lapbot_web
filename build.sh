#!/usr/bin/env bash
# exit on error
set -o errexit

echo "--- Bắt đầu quá trình Build ---"

# 1. Cài đặt các gói Node.js và build frontend
echo "-> Cài đặt các gói frontend..."
npm install

echo "-> Build tài sản Vite..."
npm run build
# Sau bước này, thư mục `vite_assets` sẽ được tạo ra.

# 2. Cài đặt các gói Python
echo "-> Cài đặt các gói backend..."
pip install -r requirements.txt

# 3. Chạy Django collectstatic
# Lệnh này sẽ tìm thư mục `vite_assets` (nhờ STATICFILES_DIRS)
# và sao chép nội dung của nó vào thư mục STATIC_ROOT (`staticfiles`).
echo "-> Chạy collectstatic..."
python manage.py collectstatic --no-input

# 4. Áp dụng các thay đổi database
echo "-> Chạy migrations..."
python manage.py migrate

echo "--- Quá trình Build hoàn tất ---"