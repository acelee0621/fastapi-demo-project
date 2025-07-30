# app/models/mixin.py
from datetime import datetime

from sqlalchemy import func
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import TIMESTAMP

class DateTimeMixin:
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),     # 用 PostgreSQL 方言，等价于 DateTime(timezone=True)
        # DateTime(timezone=True),    # 更通用的写法，你可以直接使用这个，去掉上面的 TIMESTAMP
        server_default=func.now(),    # 插入时由 PG 生成，采用服务器时间        
        insert_sentinel=False,        # 禁止 ORM 隐式写入
        nullable=False,               # 不允许为空  
        index=True,                   # 可通过创建时间索引 
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),     # 用 PostgreSQL 方言，等价于 DateTime(timezone=True)  
        # DateTime(timezone=True),    # 更通用的写法，你可以直接使用这个，去掉上面的 TIMESTAMP
        server_default=func.now(),    # 插入时由 PG 生成，采用服务器时间
        onupdate=func.now(),          # 更新时由 PG 刷新，采用服务器时间        
        insert_sentinel=False,        # 禁止 ORM 隐式写入
        nullable=False,
    )