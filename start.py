import subprocess
import sys
import os
import webbrowser
import time
import threading

def start_backend():
    """启动后端服务"""
    print("🚀 启动后端服务...")
    subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])

def open_browser():
    """延迟打开浏览器"""
    time.sleep(3)
    print("\n🌐 正在打开浏览器...")
    webbrowser.open('http://localhost:8000')

def main():
    print("=" * 50)
    print("💬 FastAPI 聊天室启动器")
    print("=" * 50)
    print()
    print("启动说明：")
    print("1. 聊天室前端: http://localhost:8000")
    print("2. API 文档: http://localhost:8000/docs")
    print("3. 数据库探索: jupyter notebook database_explorer.ipynb")
    print()
    print("-" * 50)
    
    # 在新线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.start()
    
    # 启动后端
    try:
        start_backend()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")

if __name__ == "__main__":
    main()
