import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# 测试注册
print("1. 测试注册...")
response = requests.post(f"{BASE_URL}/register", json={
    "username": "test2",
    "password": "test2"
})
print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")

# 测试登录获取token
print("\n2. 测试登录...")
response = requests.post(f"{BASE_URL}/token", data={
    "username": "test2",
    "password": "test2"
})
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"获取到token: {token[:20]}...")
else:
    print(f"响应: {response.text}")
    token = None

if token:
    # 测试发送消息
    print("\n3. 测试发送消息...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{BASE_URL}/messages/", json={
        "content": "Hello, this is a test message!"
    }, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")

    # 测试获取消息
    print("\n4. 测试获取消息...")
    response = requests.get(f"{BASE_URL}/messages/?limit=5", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")