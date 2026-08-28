import cv2
import numpy as np
import socket
import threading

# Конфигурация для приёма с нескольких камер
CAMERAS = [
    {"ip": "127.0.0.1", "port": 5000, "name": "Камера 1"},
    {"ip": "127.0.0.1", "port": 5001, "name": "Камера 2"},
    {"ip": "127.0.0.1", "port": 5002, "name": "Камера 3"},
]

def receive_camera_stream(camera_config):
    """Поток для приёма видео с одной камеры"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((camera_config["ip"], camera_config["port"]))
    sock.settimeout(1.0)
    
    print(f"{camera_config['name']}: ожидание потока на порту {camera_config['port']}...")
    
    while True:
        try:
            data, addr = sock.recvfrom(65536)
            
            # Декодирование JPEG
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                # Отображение с именем камеры
                cv2.imshow(camera_config["name"], frame)
            
        except socket.timeout:
            continue
        
        # Выход по нажатию 'q' в любом окне
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    sock.close()

# Запуск потоков для каждой камеры
threads = []
for camera in CAMERAS:
    thread = threading.Thread(target=receive_camera_stream, args=(camera,))
    threads.append(thread)
    thread.start()

# Ожидание завершения всех потоков
for thread in threads:
    thread.join()

cv2.destroyAllWindows()