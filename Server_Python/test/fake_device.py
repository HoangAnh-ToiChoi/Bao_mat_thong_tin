import socketio
import time
import random
import base64

# Kết nối đến Server (Localhost)
sio = socketio.Client()

# ID giả lập
DEVICE_ID = "FAKE_DEVICE_VIP_PRO"

@sio.event
def connect():
    print(f"✅ Đã kết nối tới Server với ID: {DEVICE_ID}")
    
    # Gửi thử 1 tấm ảnh (Base64 giả - là một chấm đỏ nhỏ xíu)
    # Đây là chuỗi base64 hợp lệ của 1 file ảnh 1x1 pixel
    fake_img_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    print(">>> Đang gửi ảnh giả...")
    sio.emit('gui_anh', {
        'device_id': DEVICE_ID,
        'img': fake_img_base64,
        'type': 'back' # Giả vờ là cam sau
    })

@sio.event
def disconnect():
    print("❌ Mất kết nối!")

@sio.on('LENH_CHUP_ANH')
def on_capture(data):
    print(f"📸 NHẬN LỆNH CHỤP ẢNH: {data}")
    # Giả vờ chụp xong gửi lại liền
    fake_img_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    sio.emit('gui_anh', {
        'device_id': DEVICE_ID,
        'img': fake_img_base64,
        'type': data.get('camera', 'back')
    })

def main():
    try:
        # Kết nối vào Server
        sio.connect('http://localhost:5000')
        
        # Vòng lặp gửi GPS liên tục để test bản đồ
        while True:
            # Tọa độ giả (Loananh quanh Đại học Cần Thơ hoặc HCM)
            # Random nhẹ để thấy nó di chuyển trên bản đồ
            lat = 10.762622 + random.uniform(-0.001, 0.001)
            long = 106.660172 + random.uniform(-0.001, 0.001)
            
            print(f"📍 Đang gửi GPS: {lat}, {long}")
            
            sio.emit('gui_toa_do', {
                'device_id': DEVICE_ID,
                'lat': lat,   # Quan trọng: Server mới cần số (float), không để ngoặc kép
                'long': long
            })
            
            time.sleep(3) # Cứ 3 giây gửi 1 lần
            
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        sio.disconnect()

if __name__ == '__main__':
    # Cần cài thư viện: pip install python-socketio[client]
    main()