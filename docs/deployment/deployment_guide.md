# EmbedAI 部署指南

## 概述

本指南详细介绍了EmbedAI管理后台系统的部署方法，包括开发环境、测试环境和生产环境的部署配置。

## 系统要求

### 最低硬件要求

| 环境 | CPU | 内存 | 存储 | 网络 |
|------|-----|------|------|------|
| 开发环境 | 2核 | 4GB | 20GB | 1Mbps |
| 测试环境 | 4核 | 8GB | 50GB | 10Mbps |
| 生产环境 | 8核 | 16GB | 200GB | 100Mbps |

### 推荐硬件配置

| 环境 | CPU | 内存 | 存储 | 网络 |
|------|-----|------|------|------|
| 开发环境 | 4核 | 8GB | 50GB | 10Mbps |
| 测试环境 | 8核 | 16GB | 100GB | 100Mbps |
| 生产环境 | 16核 | 32GB | 500GB SSD | 1Gbps |

### 软件依赖

- **操作系统**: Ubuntu 20.04+ / CentOS 8+ / macOS 12+
- **Python**: 3.11+
- **数据库**: PostgreSQL 13+ / MySQL 8.0+ / SQLite 3.35+
- **缓存**: Redis 7.0+
- **Web服务器**: Nginx 1.20+ (生产环境)
- **容器**: Docker 20.10+ / Docker Compose 2.0+

## 环境配置

### 环境变量

创建 `.env` 文件：

```bash
# 基础配置
APP_NAME=EmbedAI管理后台
APP_VERSION=1.0.0
DEBUG=false
SECRET_KEY=your-super-secret-key-here

# 数据库配置
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/embedai
# 或者使用MySQL
# DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/embedai
# 或者使用SQLite（开发环境）
# DATABASE_URL=sqlite+aiosqlite:///./embedai.db

# Redis配置
REDIS_URL=redis://localhost:6379/0

# JWT配置
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# 邮件配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=noreply@embedai.com

# 文件存储配置
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB

# 外部服务配置
LLM_API_URL=https://api.openai.com/v1
LLM_API_KEY=your-llm-api-key

# 监控配置
ENABLE_METRICS=true
METRICS_PORT=9090

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

### 开发环境配置

```bash
# 开发环境特定配置
DEBUG=true
LOG_LEVEL=DEBUG
DATABASE_URL=sqlite+aiosqlite:///./dev_embedai.db
REDIS_URL=redis://localhost:6379/1
```

### 生产环境配置

```bash
# 生产环境特定配置
DEBUG=false
LOG_LEVEL=WARNING
DATABASE_URL=postgresql+asyncpg://embedai_user:secure_password@db-server:5432/embedai_prod
REDIS_URL=redis://redis-server:6379/0
ENABLE_HTTPS=true
CORS_ORIGINS=["https://admin.embedai.com"]
```

## 部署方式

### 1. 本地开发部署

#### 步骤1: 环境准备

```bash
# 克隆项目
git clone https://github.com/your-org/embedai-admin-backend.git
cd embedai-admin-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或者
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

#### 步骤2: 数据库初始化

```bash
# 创建数据库（PostgreSQL示例）
createdb embedai_dev

# 运行数据库迁移
alembic upgrade head

# 创建初始管理员用户
python scripts/create_admin.py --email admin@example.com --password admin123
```

#### 步骤3: 启动服务

```bash
# 启动Redis（如果未运行）
redis-server

# 启动应用
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 步骤4: 验证部署

```bash
# 检查健康状态
curl http://localhost:8000/health

# 访问API文档
open http://localhost:8000/docs
```

### 2. Docker部署

#### 步骤1: 构建镜像

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 步骤2: Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://embedai:password@db:5432/embedai
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=embedai
      - POSTGRES_USER=embedai
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### 步骤3: 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f app
```

### 3. 生产环境部署

#### 步骤1: 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y nginx postgresql redis-server supervisor

# 创建应用用户
sudo useradd --create-home --shell /bin/bash embedai
sudo usermod -aG sudo embedai
```

#### 步骤2: 数据库配置

```bash
# 配置PostgreSQL
sudo -u postgres psql
CREATE DATABASE embedai_prod;
CREATE USER embedai_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE embedai_prod TO embedai_user;
\q

# 配置Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

#### 步骤3: 应用部署

```bash
# 切换到应用用户
sudo su - embedai

# 克隆代码
git clone https://github.com/your-org/embedai-admin-backend.git
cd embedai-admin-backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件设置生产环境配置

# 运行数据库迁移
alembic upgrade head

# 创建管理员用户
python scripts/create_admin.py
```

#### 步骤4: Nginx配置

```nginx
# /etc/nginx/sites-available/embedai
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static/ {
        alias /home/embedai/embedai-admin-backend/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /uploads/ {
        alias /home/embedai/embedai-admin-backend/uploads/;
        expires 1d;
    }
}
```

#### 步骤5: Supervisor配置

```ini
# /etc/supervisor/conf.d/embedai.conf
[program:embedai]
command=/home/embedai/embedai-admin-backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
directory=/home/embedai/embedai-admin-backend
user=embedai
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/embedai/app.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=PATH="/home/embedai/embedai-admin-backend/venv/bin"
```

#### 步骤6: 启动服务

```bash
# 启用Nginx站点
sudo ln -s /etc/nginx/sites-available/embedai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 启动Supervisor
sudo systemctl enable supervisor
sudo systemctl start supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start embedai

# 检查服务状态
sudo supervisorctl status
```

## 监控和日志

### 日志配置

```python
# logging_config.py
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"],
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "sqlalchemy": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

### 健康检查

```python
# health_check.py
from fastapi import APIRouter
from app.models.database import AsyncSessionLocal
from app.core.redis_manager import redis_manager

router = APIRouter()

@router.get("/health")
async def health_check():
    """系统健康检查"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    # 检查数据库连接
    try:
        async with AsyncSessionLocal() as db:
            await db.execute("SELECT 1")
        status["services"]["database"] = "healthy"
    except Exception as e:
        status["services"]["database"] = f"unhealthy: {str(e)}"
        status["status"] = "unhealthy"
    
    # 检查Redis连接
    try:
        await redis_manager.ping()
        status["services"]["redis"] = "healthy"
    except Exception as e:
        status["services"]["redis"] = f"unhealthy: {str(e)}"
        status["status"] = "unhealthy"
    
    return status
```

## 备份和恢复

### 数据库备份

```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/database"
DB_NAME="embedai_prod"
DB_USER="embedai_user"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
pg_dump -h localhost -U $DB_USER -d $DB_NAME > $BACKUP_DIR/embedai_$DATE.sql

# 压缩备份文件
gzip $BACKUP_DIR/embedai_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "embedai_*.sql.gz" -mtime +7 -delete

echo "数据库备份完成: embedai_$DATE.sql.gz"
```

### 应用备份

```bash
#!/bin/bash
# backup_app.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/application"
APP_DIR="/home/embedai/embedai-admin-backend"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份应用文件
tar -czf $BACKUP_DIR/app_$DATE.tar.gz \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs' \
    -C $APP_DIR .

# 备份上传文件
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz -C $APP_DIR uploads/

# 删除30天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "应用备份完成: app_$DATE.tar.gz, uploads_$DATE.tar.gz"
```

### 恢复流程

```bash
# 数据库恢复
gunzip embedai_20240805_120000.sql.gz
psql -h localhost -U embedai_user -d embedai_prod < embedai_20240805_120000.sql

# 应用恢复
sudo supervisorctl stop embedai
tar -xzf app_20240805_120000.tar.gz -C /home/embedai/embedai-admin-backend/
tar -xzf uploads_20240805_120000.tar.gz -C /home/embedai/embedai-admin-backend/
sudo supervisorctl start embedai
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查数据库状态
   sudo systemctl status postgresql
   
   # 检查连接配置
   psql -h localhost -U embedai_user -d embedai_prod
   ```

2. **Redis连接失败**
   ```bash
   # 检查Redis状态
   sudo systemctl status redis-server
   
   # 测试连接
   redis-cli ping
   ```

3. **应用启动失败**
   ```bash
   # 查看应用日志
   sudo supervisorctl tail -f embedai
   
   # 检查配置文件
   python -c "from app.core.config import settings; print(settings.DATABASE_URL)"
   ```

4. **Nginx配置错误**
   ```bash
   # 测试Nginx配置
   sudo nginx -t
   
   # 查看错误日志
   sudo tail -f /var/log/nginx/error.log
   ```

### 性能调优

1. **数据库优化**
   ```sql
   -- 查看慢查询
   SELECT query, mean_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_time DESC 
   LIMIT 10;
   
   -- 分析表统计信息
   ANALYZE;
   ```

2. **应用优化**
   ```bash
   # 调整worker数量
   uvicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
   
   # 启用gzip压缩
   # 在Nginx配置中添加
   gzip on;
   gzip_types text/plain application/json application/javascript text/css;
   ```

## 安全加固

### SSL/TLS配置

```bash
# 使用Let's Encrypt获取免费SSL证书
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 防火墙配置

```bash
# 配置UFW防火墙
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # 禁止外部访问数据库
sudo ufw deny 6379/tcp  # 禁止外部访问Redis
```

### 系统安全

```bash
# 禁用root登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 配置fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```
