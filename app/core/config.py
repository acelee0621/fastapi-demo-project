# /fastapi-demo-project/app/core/config.py

from functools import lru_cache
from typing import Literal

# 使用 Python 3.8+ 内置的 importlib.metadata
from importlib import metadata

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


# --- 动态版本号获取 ---
def get_project_version() -> str:
    """从 pyproject.toml 文件中动态读取项目版本号。"""
    try:
        # "fastapi-demo-project" 必须与你在 pyproject.toml 中定义的 [project] name 完全匹配
        return metadata.version("fastapi-demo-project")
    except metadata.PackageNotFoundError:
        # 如果包没有被 "安装" (例如，在 Docker 构建的早期阶段或非标准环境中)
        # 提供一个合理的回退值。
        return "0.1.0-dev"


# --- 嵌套配置模型 ---
# 这是一个最佳实践，它将相关的配置分组，使结构更清晰。


class DatabaseSettings(BaseSettings):
    """数据库相关配置"""

    HOST: str = "localhost"
    PORT: int = 5432
    USER: str = "postgres"
    PASSWORD: str = "postgres"
    DB: str = "app"

    # 使用 @computed_field，可以在模型内部根据其他字段动态生成新字段
    # 这比在模型外部手动拼接字符串要优雅得多。
    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """生成异步 PostgreSQL 连接字符串。"""
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"

    # model_config 的设置在这里同样适用，用于 Pydantic 如何加载这些设置
    model_config = SettingsConfigDict(env_prefix="DEMO_DB_")


class Settings(BaseSettings):
    """主配置类，汇集所有配置项。"""

    # 环境配置: 'dev' 或 'prod'
    # Literal 类型确保了 ENVIRONMENT 只能是指定的值之一，增加了类型安全
    ENVIRONMENT: Literal["dev", "prod"] = "dev"

    DEBUG: bool = False
    APP_NAME: str = "FastAPI Demo Project"

    # --- 嵌套配置 ---
    # 将 DatabaseSettings 作为主 Settings 的一个字段。
    # Pydantic 会自动处理带有 'DEMO_DB_' 前缀的环境变量，并填充到这个模型中。
    DB: DatabaseSettings = DatabaseSettings()

    # Pydantic-settings 的核心配置
    model_config = SettingsConfigDict(
        # 从 .env 文件加载环境变量,这里不写，放到动态加载了
        env_file_encoding="utf-8",
        # 为顶层配置项设置前缀
        env_prefix="DEMO_",
        # 允许大小写不敏感的环境变量
        case_sensitive=False,
    )


# --- 缓存与依赖注入 ---
# 这是整个配置系统的关键入口点。
@lru_cache
def get_settings() -> Settings:
    """
    创建并返回一个配置实例。

    使用 @lru_cache 装饰器实现以下目标：
    1. 性能: 配置只在应用启动时被加载和解析一次，而不是在每个请求中。
    2. 一致性 (单例): 应用的任何部分调用此函数都将获得完全相同的配置对象实例。

    这意味着，如果你在应用运行时更改了 .env 文件，你需要重启应用才能使更改生效。
    """
    print("正在加载配置...")  # 这条消息只会在应用首次启动时打印一次

    # 根据 ENVIRONMENT 环境变量来决定加载哪个 .env 文件
    # 这是一个非常灵活的模式
    import os

    print("正在加载配置...")  # 这条消息只会在应用首次启动时打印一次

    # 根据 ENVIRONMENT 环境变量来决定加载哪个 .env 文件
    # 这是一个非常灵活的模式
    env = os.getenv("ENVIRONMENT", "dev")

    env_file = f".env.{env}"

    # 动态创建 Settings 实例，并指定正确的 env_file

    settings = Settings(_env_file=env_file)  # type: ignore

    print(f"成功加载 '{env}' 环境配置 for {settings.APP_NAME}")
    return settings


# 在应用启动时就创建一个实例，方便在非 FastAPI 上下文中使用
settings = get_settings()
