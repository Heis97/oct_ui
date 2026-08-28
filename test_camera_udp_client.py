import cv2
import socket
import numpy as np

# Настройка сокета
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("127.0.0.1", 12345)) # Слушать на порту

while True:
    packet, _ = server_socket.recvfrom(65535) # Макс размер UDP
    
    # Декодирование
    data = np.frombuffer(packet, dtype=np.uint8)
    frame = cv2.imdecode(data, 1)
    
    if frame is not None:
        cv2.imshow('Receiving', frame)
        
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()