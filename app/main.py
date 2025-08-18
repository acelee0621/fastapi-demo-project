# app/main.py
from loguru import logger
from fastapi import Depends, FastAPI, Response
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_pagination import add_pagination

# 从 config 模块导入 get_settings 函数和 get_project_version 函数
from app.core.config import Settings, get_settings, get_project_version, settings

# 从 core.database 模块导入 setup_database_connection 和 close_database_connection 函数
from app.core.database import (
    setup_database_connection,
    close_database_connection,
    get_db,
)
from app.core.exceptions import global_exception_handler
from app.api.v1 import heroes_route, auth_route, collections_route
from app.lifespan import lifespan


# Lifespan: 在应用启动时调用 get_settings，触发配置加载和缓存
# 当 Lifspan 开始变得臃肿，可以考虑拆分成多个文件
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # 应用启动时执行
#     get_settings()
#     await setup_database_connection()

#     logger.info("🚀 应用启动，数据库已连接。")
#     yield
#     # 应用关闭时执行
#     await close_database_connection()
#     logger.info("应用关闭，数据库连接已释放。")


app = FastAPI(
    title=settings.APP_NAME,
    description="这是一个 FastAPI 演示项目",
    # 动态从 pyproject.toml 读取版本号
    version=get_project_version(),
    lifespan=lifespan,
)

# 全局异常处理,所有未被自定义异常处理的异常都会触发
app.add_exception_handler(Exception, global_exception_handler)


# 路由引入
app.include_router(auth_route.router, prefix="/api/v1")
app.include_router(heroes_route.router, prefix="/api/v1")
app.include_router(collections_route.router, prefix="/api/v1")

# 添加分页支持
add_pagination(app)


@app.get("/health")
async def health_check(response: Response):
    response.status_code = 200
    return {"status": "ok 👍 "}


@app.get("/")
def read_root(
    # 使用 FastAPI 的依赖注入系统来获取配置实例
    # FastAPI 会自动调用 get_settings()，由于缓存的存在，这几乎没有开销
    settings: Settings = Depends(get_settings),
):
    """
    一个示例端点，演示如何访问配置。
    """
    return {
        "message": f"Hello from the {settings.APP_NAME}!",
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG,
        # 演示如何访问嵌套的配置项
        "database_host": settings.DB.HOST,
        # 演示如何使用在模型中动态计算的属性
        "database_url_hidden_password": settings.DB.DATABASE_URL.replace(
            settings.DB.PASSWORD, "****"
        ),
        "app_version": get_project_version(),
    }


@app.get("/db-check")
async def db_check(db: AsyncSession = Depends(get_db)):
    """
    一个简单的端点，用于检查数据库连接是否正常工作。
    """
    try:
        # 执行一个简单的查询来验证连接
        result = await db.execute(text("SELECT 1"))
        if result.scalar_one() == 1:
            return {"status": "ok", "message": "数据库连接成功！"}
    except Exception as e:
        return {"status": "error", "message": f"数据库连接失败: {e}"}
