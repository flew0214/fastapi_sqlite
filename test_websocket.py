import websocket
import threading
import time
import json

def on_message(ws, message):
    print(f"📨 收到: {message}")

def on_error(ws, error):
    print(f"❌ 错误: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"🔒 连接关闭: {close_status_code} - {close_msg}")

def on_open(ws):
    print("✅ WebSocket 连接成功!")
    
    # 发送一条消息
    ws.send("MESSAGE:Hello from test!")
    
    # 保持连接
    def run():
        time.sleep(5)
        ws.close()
    
    threading.Thread(target=run).start()

# 测试 WebSocket 连接
# 先获取 token
import requests

print("1. 注册测试用户...")
resp = requests.post("http://localhost:8000/register", json={
    "username": "testuser",
    "password": "testpass"
})
if resp.status_code == 200:
    print("✅ 用户注册成功")
    user = resp.json()
    print(f"   用户ID: {user['id']}")
else:
    print(f"❌ 注册失败: {resp.text}")
    exit(1)

print("\n2. 登录获取 token...")
resp = requests.post("http://localhost:8000/token", data={
    "username": "testuser",
    "password": "testpass"
})
if resp.status_code == 200:
    token = resp.json()["access_token"]
    print("✅ 登录成功")
    print(f"   Token: {token[:50]}...")
else:
    print(f"❌ 登录失败: {resp.text}")
    exit(1)

print("\n3. 测试 WebSocket 连接...")
ws_url = f"ws://localhost:8000/ws/{token}"
print(f"   连接地址: {ws_url}")

ws = websocket.WebSocketApp(
    ws_url,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close
)

ws.run_forever()