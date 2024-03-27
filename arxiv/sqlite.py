import sqlite3

# Kết nối đến cơ sở dữ liệu SQLite
conn = sqlite3.connect('downloaded_ids.db')
cursor = conn.cursor()

# Tạo bảng để lưu trữ các ID đã tải
cursor.execute('''CREATE TABLE IF NOT EXISTS downloaded_ids (
                    id TEXT PRIMARY KEY
                )''')

# Đóng kết nối
conn.close()
