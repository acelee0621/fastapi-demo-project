# app/models/__init__.py

# 写法 1 ：手动导入
from .base import Base
from .users import User
from .heroes import Hero
from .collections import Collection

# 可选：声明公开接口（清晰化模块导出）
__all__ = ["Base", "User", "Hero", "Collection"]


# 写法 2：动态导入
# import importlib
# import pkgutil

# from .base import Base

# # 把当前包（models）下除了 base.py 以外的所有 .py 文件都 import 一遍
# for _, modelname, _ in pkgutil.iter_modules(__path__):
#     if modelname != "base":
#         importlib.import_module(f"{__name__}.{modelname}")

# __all__ = ["Base"]
