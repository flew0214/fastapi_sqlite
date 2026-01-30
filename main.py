from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from uuid import uuid4
import os
import logging
import models
import schemas
from models import Base, User, Message

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = "sqlite:///./chat.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

init_db()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(title="Chat Room API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

class ConnectionManager:
    def __init__(self):
        # session_id -> (websocket, username)
        self.active_connections: Dict[str, Tuple[WebSocket, str]] = {}

    def cleanup_closed_connections(self):
        """清理已关闭的 WebSocket 连接"""
        closed_sessions = []
        for session_id, (connection, username) in self.active_connections.items():
            try:
                # 检查连接状态
                state = connection.client_state.name
                if state != "CONNECTED":
                    closed_sessions.append(session_id)
            except Exception:
                # 连接异常，标记移除
                closed_sessions.append(session_id)

        for session_id in closed_sessions:
            logger.debug(f"清理失效连接: {session_id[:8]}")
            if session_id in self.active_connections:
                del self.active_connections[session_id]

        return len(closed_sessions)

    async def connect(self, websocket: WebSocket, username: str) -> str:
        # 连接前先清理失效的连接
        self.cleanup_closed_connections()

        await websocket.accept()
        session_id = str(uuid4())
        self.active_connections[session_id] = (websocket, username)
        logger.info(f"添加新连接: {username} (session: {session_id[:8]})")

        # 清理后再次广播用户列表
        await self.broadcast_user_list()
        return session_id

    def disconnect(self, session_id: str):
        logger.info(f"断开连接请求: {session_id[:8]}")
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"已移除连接: {session_id[:8]}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_user_list(self):
        # 先清理失效连接
        self.cleanup_closed_connections()

        # 收集所有唯一的用户名
        user_list = set()
        for session_id, (connection, username) in self.active_connections.items():
            try:
                # double check connection state
                if connection.client_state.name == "CONNECTED":
                    user_list.add(username)
            except Exception:
                # 连接异常，应该已被清理，跳过
                continue

        if not user_list:
            return

        message = f"USER_LIST:{','.join(sorted(user_list))}"
        failed_sessions = []

        for session_id, (connection, username) in self.active_connections.items():
            try:
                if connection.client_state.name == "CONNECTED":
                    await connection.send_text(message)
            except Exception as e:
                logger.debug(f"发送用户列表失败 {session_id[:8]}: {e}")
                failed_sessions.append(session_id)

        # 清理发送失败的连接
        for session_id in failed_sessions:
            if session_id in self.active_connections:
                del self.active_connections[session_id]

        logger.debug(f"广播用户列表: {user_list}")

    async def broadcast_message(self, message: str):
        # 先清理失效连接
        self.cleanup_closed_connections()

        failed_sessions = []
        for session_id, (connection, username) in self.active_connections.items():
            try:
                if connection.client_state.name == "CONNECTED":
                    await connection.send_text(message)
            except Exception as e:
                logger.debug(f"发送消息失败 {session_id[:8]}: {e}")
                failed_sessions.append(session_id)

        # 清理发送失败的连接
        for session_id in failed_sessions:
            if session_id in self.active_connections:
                del self.active_connections[session_id]

manager = ConnectionManager()

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    logger.info(f"WebSocket 连接尝试, token 长度: {len(token)}")

    # 先清理所有失效的连接
    closed_count = manager.cleanup_closed_connections()
    if closed_count > 0:
        logger.info(f"清理了 {closed_count} 个失效连接")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("WebSocket 连接失败: token 中没有用户名")
            await websocket.close(code=4001)
            return
        logger.info(f"WebSocket 用户认证成功: {username}")
    except JWTError as e:
        logger.error(f"WebSocket JWT 验证失败: {e}")
        await websocket.close(code=4001)
        return

    session_id = await manager.connect(websocket, username)
    logger.info(f"WebSocket 连接建立: {username} (session: {session_id[:8]}), 当前在线数: {len(manager.active_connections)}")
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                
                # 忽略心跳消息
                if data == "PING":
                    await websocket.send_text("PONG")
                    continue
                    
                logger.debug(f"收到消息 from {username}: {data[:50]}...")
                
                if data.startswith("MESSAGE:"):
                    message_content = data[8:]
                    if not message_content.strip():
                        continue
                        
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.username == username).first()
                        if user:
                            db_message = Message(content=message_content, user_id=user.id)
                            db.add(db_message)
                            db.commit()
                            timestamp = db_message.created_at.strftime("%H:%M")
                            broadcast_msg = f"NEW_MESSAGE:{username}:{message_content}:{timestamp}"
                            await manager.broadcast_message(broadcast_msg)
                            logger.info(f"消息广播: {username} -> {message_content[:30]}...")
                    except Exception as e:
                        logger.error(f"保存消息失败: {e}")
                        db.rollback()
                    finally:
                        db.close()
            except Exception as e:
                logger.error(f"处理消息失败: {e}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        await manager.broadcast_user_list()
        logger.info(f"WebSocket 断开: {username} (session: {session_id[:8]}), 当前在线数: {len(manager.active_connections)}")

@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already registered")

@app.post("/token", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/messages/", response_model=schemas.MessageResponse)
def send_message(message: schemas.MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_message = Message(content=message.content, user_id=current_user.id)
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return schemas.MessageResponse(
        id=db_message.id,
        content=db_message.content,
        user_id=db_message.user_id,
        username=current_user.username,
        created_at=db_message.created_at
    )

@app.get("/messages/", response_model=List[schemas.MessageResponse])
def get_messages(limit: int = 50, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(Message, User.username).join(User, Message.user_id == User.id).order_by(Message.created_at.desc()).limit(limit).all()
    result = []
    for msg, username in messages:
        result.append(schemas.MessageResponse(
            id=msg.id,
            content=msg.content,
            user_id=msg.user_id,
            username=username,
            created_at=msg.created_at
        ))
    return result[::-1]

@app.delete("/messages/all")
def clear_all_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """清空所有历史消息"""
    try:
        count = db.query(Message).count()
        db.query(Message).delete()
        db.commit()
        logger.info(f"用户 {current_user.username} 清空了 {count} 条历史消息")
        return {"detail": f"Cleared {count} messages"}
    except Exception as e:
        logger.error(f"清空消息失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to clear messages")

@app.delete("/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this message")
    db.delete(message)
    db.commit()
    return {"detail": "Message deleted"}

@app.get("/users/me", response_model=schemas.UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.get("/users/online")
def get_online_users():
    # 收集所有唯一的用户名
    user_list = set()
    for session_id, (connection, username) in manager.active_connections.items():
        user_list.add(username)
    return {"online_users": list(user_list)}

@app.get("/")
async def root():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/{path:path}")
async def serve_static(path: str):
    file_path = os.path.join(STATIC_DIR, path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))