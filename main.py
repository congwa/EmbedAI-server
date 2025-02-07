from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import admin, client
from app.models.database import Base, engine
from app.core.exceptions import (
    HTTPException,
    ValidationError,
    SQLAlchemyError,
    http_exception_handler,
    sqlalchemy_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.core.middleware import LoggingMiddleware, RequestValidationMiddleware
from app.core.logger import Logger

from fast_graphrag import GraphRAG, QueryParam


def main():
    """主函数"""
    # load_dotenv()  # 加载环境变量
    
    # # # 指定要处理的目录
    # # target_dir = working_dir
    # # if target_dir.exists():
    # #     print(f"开始处理目录: {target_dir}")
    # #     insert_files(target_dir)
    # # else:
    # #     print(f"目录不存在: {target_dir}")

    # # 测试查询
    # params = QueryParam(
    #     with_references=True,  # 是否包含参考资料
    #     only_context=True,    # 是否只返回上下文
    #     entities_max_tokens=4000,  # 实体最大token数
    #     relationships_max_tokens=3000,  # 关系最大token数
    #     chunks_max_tokens=9000  # 文本块最大token数
    # )
    # test_query = "嵌入模型在里面干了什么，涉及哪些文件"
    # result = grag.query(test_query, params)
    
    # print("\n" + "="*50)
    # print(f"📝 查询问题: {test_query}")
    # print("="*50)
    
    # print("\n🔍 查询结果:")
    # print("-"*30)
    # print(f"回答内容:\n{result.response}")
    
    # print("\n📊 上下文信息:")
    # print("-"*30)
    # print("\n实体列表:")
    # for entity in result.context.entities:
    #     print(f"- {entity}")
        
    # print("\n关系列表:")
    # for relation in result.context.relationships:
    #     print(f"- {relation}")
        
    # print("\n相关文本块:")
    # for chunk in result.context.chunks:
    #     print(f"- {chunk}")

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 初始化应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 注册异常处理器
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestValidationMiddleware)

# 注册路由
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(client.router, prefix=settings.API_V1_STR)

# 启动事件
@app.on_event("startup")
async def startup_event():
    Logger.info("Application starting up...")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    Logger.info("Application shutting down...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)