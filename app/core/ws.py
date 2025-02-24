import asyncio
import json
from typing import Dict, Set, Optional
from datetime import datetime, timedelta
from fastapi import WebSocket, FastAPI
from app.core.redis_manager import redis_manager
from app.core.logger import Logger

class ConnectionManager:
    """WebSocket连接管理器
    
    功能：
    1. 管理WebSocket连接池
    2. 心跳检测
    3. 连接状态监控
    4. 自动重连机制
    """
    
    def __init__(self):
        # 活跃连接: chat_id -> {client_id -> connection}
        self.active_connections: Dict[int, Dict[str, "WSConnection"]] = {}
        # 心跳检测间隔（秒）
        self.heartbeat_interval = 30
        # 连接超时时间（秒）
        self.connection_timeout = 60
        # 重试次数
        self.max_retry_attempts = 3
        # 重试间隔（秒）
        self.retry_interval = 5
        
    async def connect(
        self,
        chat_id: int,
        client_id: str,
        websocket: WebSocket,
        is_admin: bool = False
    ) -> None:
        """建立新的WebSocket连接"""
        await websocket.accept()
        
        # 创建连接包装器
        connection = WSConnection(
            websocket=websocket,
            client_id=client_id,
            is_admin=is_admin,
            manager=self
        )
        
        # 保存连接
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = {}
        self.active_connections[chat_id][client_id] = connection
        
        # 启动心跳检测
        asyncio.create_task(connection.start_heartbeat())
        
        # 记录连接信息到Redis
        await redis_manager.store_ws_connection(
            chat_id=chat_id,
            client_id=client_id,
            connection_info={
                "connected_at": datetime.now(),
                "is_admin": is_admin,
                "last_heartbeat": datetime.now()
            }
        )
        
        Logger.info(f"New WebSocket connection: chat_id={chat_id}, client_id={client_id}")
        
    def disconnect(self, chat_id: int, client_id: str) -> None:
        """断开WebSocket连接"""
        if chat_id in self.active_connections:
            connection = self.active_connections[chat_id].pop(client_id, None)
            if connection:
                connection.stop_heartbeat()
            if not self.active_connections[chat_id]:
                self.active_connections.pop(chat_id)
                
            # 从Redis中移除连接信息
            asyncio.create_task(
                redis_manager.remove_ws_connection(chat_id, client_id)
            )
                
        Logger.info(f"WebSocket disconnected: chat_id={chat_id}, client_id={client_id}")
        
    async def broadcast_to_chat(
        self,
        chat_id: int,
        message: dict,
        exclude_client: str = None,
        retry_count: int = 0
    ) -> None:
        """广播消息到聊天会话的所有连接
        
        包含重试机制，在发送失败时自动重试
        """
        if chat_id in self.active_connections:
            for client_id, connection in self.active_connections[chat_id].items():
                if client_id != exclude_client:
                    try:
                        await connection.send_message(message)
                    except Exception as e:
                        Logger.error(f"Failed to send message: {e}")
                        if retry_count < self.max_retry_attempts:
                            await asyncio.sleep(self.retry_interval)
                            await self.broadcast_to_chat(
                                chat_id,
                                message,
                                exclude_client,
                                retry_count + 1
                            )
                            
    async def get_chat_connections(self, chat_id: int) -> Dict[str, dict]:
        """获取聊天会话的所有连接信息"""
        return await redis_manager.get_ws_connections(chat_id)
        
    async def monitor_connections(self) -> None:
        """监控所有连接状态"""
        while True:
            try:
                for chat_id in list(self.active_connections.keys()):
                    for client_id in list(self.active_connections[chat_id].keys()):
                        connection = self.active_connections[chat_id][client_id]
                        if connection.is_stale():
                            Logger.warning(f"Stale connection detected: chat_id={chat_id}, client_id={client_id}")
                            self.disconnect(chat_id, client_id)
                            
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                Logger.error(f"Error in connection monitoring: {e}")
                await asyncio.sleep(5)

class WSConnection:
    """WebSocket连接包装器
    
    提供单个连接的管理功能：
    1. 心跳检测
    2. 状态监控
    3. 消息重试
    """
    
    def __init__(
        self,
        websocket: WebSocket,
        client_id: str,
        is_admin: bool,
        manager: ConnectionManager
    ):
        self.websocket = websocket
        self.client_id = client_id
        self.is_admin = is_admin
        self.manager = manager
        self.last_heartbeat = datetime.now()
        self.is_alive = True
        self._heartbeat_task: Optional[asyncio.Task] = None
        
    async def send_message(self, message: dict, retry_count: int = 0) -> None:
        """发送消息，包含重试机制"""
        try:
            await self.websocket.send_json(message)
        except Exception as e:
            if retry_count < self.manager.max_retry_attempts:
                await asyncio.sleep(self.manager.retry_interval)
                await self.send_message(message, retry_count + 1)
            else:
                raise e
                
    async def send_heartbeat(self) -> None:
        """发送心跳包"""
        try:
            await self.websocket.send_json({"type": "ping"})
            self.last_heartbeat = datetime.now()
            
            # 更新Redis中的心跳时间
            chat_id = next(
                (cid for cid, clients in self.manager.active_connections.items()
                 if self.client_id in clients),
                None
            )
            if chat_id:
                await redis_manager.store_ws_connection(
                    chat_id=chat_id,
                    client_id=self.client_id,
                    connection_info={
                        "connected_at": self.last_heartbeat,
                        "is_admin": self.is_admin,
                        "last_heartbeat": self.last_heartbeat
                    }
                )
        except Exception as e:
            Logger.error(f"Heartbeat failed for client {self.client_id}: {e}")
            self.is_alive = False
            
    async def start_heartbeat(self) -> None:
        """启动心跳检测"""
        async def heartbeat_loop():
            while self.is_alive:
                await self.send_heartbeat()
                await asyncio.sleep(self.manager.heartbeat_interval)
                
        self._heartbeat_task = asyncio.create_task(heartbeat_loop())
        
    def stop_heartbeat(self) -> None:
        """停止心跳检测"""
        self.is_alive = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            
    def is_stale(self) -> bool:
        """检查连接是否过期"""
        return (
            not self.is_alive or
            datetime.now() - self.last_heartbeat >
            timedelta(seconds=self.manager.connection_timeout)
        )

# 创建全局连接管理器实例
connection_manager = ConnectionManager()

async def start_monitoring_connections():
    await connection_manager.monitor_connections()

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_monitoring_connections()) 