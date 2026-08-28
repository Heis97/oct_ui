#!/usr/bin/env python3
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import paho.mqtt.client as mqtt

# ===== Конфигурация MQTT =====
MQTT_HOST = "192.168.42.1"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASSWORD = None

# Имена устройств (MQTT топики)
DEVICES = {
    "mr6c_1": "wb-mr6c_197",
    "mr6c_2": "wb-mr6c_174",
}
CHANNELS_PER_DEVICE = 6

# Глобальное хранилище состояний
states = {dev: {ch: False for ch in range(1, CHANNELS_PER_DEVICE+1)} for dev in DEVICES}
states_lock = threading.Lock()

# ===== MQTT клиент =====
def on_connect(client, userdata, flags, reason_code, properties):
    print("MQTT connected")
    for dev_name in DEVICES.values():
        client.subscribe(f"/devices/{dev_name}/controls/+")

def on_message(client, userdata, msg):
    parts = msg.topic.split('/')
    if len(parts) >= 5 and parts[4].startswith('K'):
        device_name = parts[2]
        control = parts[4]
        device_id = None
        for key, val in DEVICES.items():
            if val == device_name:
                device_id = key
                break
        if not device_id:
            return
        try:
            channel = int(control[1:])
        except:
            return
        payload = msg.payload.decode()
        new_state = payload.lower() in ("1", "true", "on")
        with states_lock:
            if states[device_id][channel] != new_state:
                states[device_id][channel] = new_state
                print(f"Updated: {device_id} K{channel} = {new_state}")

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
if MQTT_USER:
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

def mqtt_loop():
    mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    mqtt_client.loop_forever()

threading.Thread(target=mqtt_loop, daemon=True).start()

# ===== HTTP сервер =====
class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        elif self.path == '/state':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            with states_lock:
                self.wfile.write(json.dumps(states).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/set':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                device = data.get('device')
                channel = data.get('channel')
                state = data.get('state')
                if device not in DEVICES:
                    raise ValueError("Неизвестное устройство")
                if not (1 <= channel <= CHANNELS_PER_DEVICE):
                    raise ValueError("Неверный канал")
                topic = f"/devices/{DEVICES[device]}/controls/K{channel}/on"
                payload = "1" if state else "0"
                mqtt_client.publish(topic, payload)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        elif self.path == '/shutdown':
            def shutdown_server():
                self.server.shutdown()
            threading.Thread(target=shutdown_server, daemon=True).start()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "shutting down"}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

# HTML-страница с увеличенной в два раза высотой кнопок, единой высотой для всех кнопок
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Управление модификацией шовных нитей</title>
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            min-height: 100vh;
            background: #0a0a0a;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            width: 90%;
            max-width: 1400px;
            background: #1e1e1e;
            border-radius: 32px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.6);
            padding: 40px 30px 50px 30px;
            border: 1px solid #333;
        }
        h1 {
            text-align: center;
            font-size: 2.2rem;
            color: #f0f0f0;
            margin-bottom: 50px;
            font-weight: 600;
            letter-spacing: 1.5px;
        }
        /* Две колонки с отступами 5% */
        .two-columns {
            display: flex;
            justify-content: space-between;
            gap: 5%;
            padding-left: 5%;
            padding-right: 5%;
            margin-bottom: 40px;
        }
        .column {
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        /* Общий стиль для всех больших кнопок (устройства и управления) */
        .relay-button, .control-all, .shutdown {
            width: 100%;
            border: none;
            border-radius: 60px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 8px 16px rgba(0,0,0,0.4);
            text-align: center;
            font-weight: bold;
            /* Единая высота: padding увеличен в 2 раза по сравнению с предыдущим (было 50px, стало 100px) */
            padding: 100px 0;
            font-size: 3.5rem;
        }
        /* Отдельные цвета для кнопок устройств */
        .relay-button {
            background-color: #2c2c2c;
            color: white;
        }
        .relay-button.on {
            background-color: #2e7d32;
            border-bottom: 6px solid #1b5e20;
        }
        .relay-button.off {
            background-color: #c62828;
            border-bottom: 6px solid #8b0000;
        }
        .relay-button:active, .control-all:active, .shutdown:active {
            transform: scale(0.97);
        }
        /* Кнопки управления */
        .control-all {
            background-color: #1565c0;
            color: white;
            margin-top: 20px;
        }
        /* Контейнер для кнопки завершения работы (ширина как у двух колонок) */
        .shutdown-wrapper {
            padding-left: 5%;
            padding-right: 5%;
        }
        .shutdown {
            background-color: #ff5722;
            color: white;
            margin-top: 20px;
        }
        .error {
            text-align: center;
            color: #ff8a80;
            margin-top: 30px;
            font-weight: 500;
            font-size: 1.2rem;
        }
        /* Адаптивность: уменьшаем высоту и шрифт на узких экранах */
        @media (max-width: 900px) {
            .relay-button, .control-all, .shutdown {
                padding: 70px 0;
                font-size: 2.5rem;
            }
            h1 {
                font-size: 1.8rem;
            }
        }
        @media (max-width: 600px) {
            .relay-button, .control-all, .shutdown {
                padding: 50px 0;
                font-size: 1.8rem;
            }
            .container {
                padding: 20px 15px 30px 15px;
            }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>Панель управления установками модификации шовных нитей</h1>
    <div class="two-columns">
        <div class="column" id="col1"></div>
        <div class="column" id="col2"></div>
    </div>
    <div class="shutdown-wrapper">
        <button class="shutdown" id="shutdownBtn">Завершить работу</button>
    </div>
    <div id="error" class="error"></div>
</div>

<script>
    // Соответствие кнопок (1..10) -> (device, channel)
    const relayMapping = [
        { device: "mr6c_1", channel: 1 },  // Устройство 1
        { device: "mr6c_1", channel: 2 },  // 2
        { device: "mr6c_1", channel: 3 },  // 3
        { device: "mr6c_1", channel: 4 },  // 4
        { device: "mr6c_1", channel: 5 },  // 5
        { device: "mr6c_1", channel: 6 },  // 6
        { device: "mr6c_2", channel: 1 },  // 7
        { device: "mr6c_2", channel: 2 },  // 8
        { device: "mr6c_2", channel: 3 },  // 9
        { device: "mr6c_2", channel: 4 }   // 10
    ];
    const totalRelays = 10;
    let states = {};

    async function fetchStates() {
        try {
            const resp = await fetch('/state');
            states = await resp.json();
            renderButtons();
            document.getElementById('error').innerText = '';
        } catch (e) {
            document.getElementById('error').innerText = 'Ошибка загрузки состояния';
            console.error(e);
        }
    }

    async function setRelay(device, channel, newState) {
        try {
            const resp = await fetch('/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device, channel, state: newState })
            });
            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.error || 'Ошибка сервера');
            }
            setTimeout(fetchStates, 100);
        } catch (e) {
            document.getElementById('error').innerText = 'Ошибка: ' + e.message;
        }
    }

    async function controlAll(state) {
        const startBtn = document.getElementById('startAllBtn');
        const stopBtn = document.getElementById('stopAllBtn');
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = true;
        for (let i = 0; i < totalRelays; i++) {
            const { device, channel } = relayMapping[i];
            await setRelay(device, channel, state);
            await new Promise(r => setTimeout(r, 50));
        }
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = false;
        await fetchStates();
    }

    function renderButtons() {
        const col1 = document.getElementById('col1');
        const col2 = document.getElementById('col2');
        let html1 = '', html2 = '';
        // Кнопки 1-5 в левую колонку, 6-10 в правую
        for (let i = 0; i < totalRelays; i++) {
            const { device, channel } = relayMapping[i];
            const state = (states[device] && states[device][channel]) || false;
            const btnClass = state ? 'on' : 'off';
            const buttonHtml = `<button class="relay-button ${btnClass}" onclick="setRelay('${device}', ${channel}, ${!state})">Устройство ${i+1}</button>`;
            if (i < 5) {
                html1 += buttonHtml;
            } else {
                html2 += buttonHtml;
            }
        }
        // Кнопки управления всех устройств (такой же высоты)
        html1 += `<button class="control-all" id="startAllBtn" onclick="controlAll(true)">Запустить все устройства</button>`;
        html2 += `<button class="control-all" id="stopAllBtn" onclick="controlAll(false)">Остановить все устройства</button>`;
        col1.innerHTML = html1;
        col2.innerHTML = html2;
    }

    document.getElementById('shutdownBtn').addEventListener('click', async () => {
        if (confirm('Вы уверены, что хотите остановить сервер?')) {
            try {
                const resp = await fetch('/shutdown', { method: 'POST' });
                const data = await resp.json();
                document.getElementById('error').innerText = data.status || 'Сервер останавливается...';
                setTimeout(() => { window.location.href = '/shutdown'; }, 500);
            } catch (e) {
                document.getElementById('error').innerText = 'Ошибка при остановке сервера';
            }
        }
    });

    fetchStates();
    setInterval(fetchStates, 2000);
</script>
</body>
</html>"""

def run_server(port=5000):
    server = ThreadingHTTPServer(('0.0.0.0', port), RequestHandler)
    print(f"HTTP сервер запущен на порту {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
        server.shutdown()

if __name__ == '__main__':
    run_server()