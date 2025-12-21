import socketio
import time
import random
from datetime import datetime


# Tạo client
sio = socketio.Client()

# chuỗi ảnh giả để test
fake_img_data = "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="

@sio.event
def connect():
    print(" >>>>> GIẢ LẬP: Đã kết nối thành công đến server")

@sio.event
def server_log(data):
    print(f"SERVER PHẢN HỒI: {data}")

def chay_gia_lap():
    try:
        sio.connect('http://localhost:5000')

        while True:
            goi_gps = {
                'device.id': 'DT_Cua_HA',
                'lat': 10.762 + random.uniform(-0.001, 0.001),
                'long': 106.662 + random.uniform(-0.001, 0.001),
                'battery': f"{random.randint(20, 100)}%"
            }
            sio.emit('gui_toa_do', goi_gps)
            print(f"ĐÃ GỬI GPS: {goi_gps['lat']}, {goi_gps['long']}")

            goi_tin_anh = {
                'device.id': 'DT_Cua_HA',
                'img': fake_img_data
            }
            sio.emit('gui_anh', goi_tin_anh)
            print(f"ĐÃ GỬI ẢNH: {goi_tin_anh['img']}")
            print("-" * 30)
            time.sleep(5)
    except Exception as e:
        print("Lỗi kết nối (Server chưa bật à??)", e)

if __name__ == '__main__':
    chay_gia_lap()