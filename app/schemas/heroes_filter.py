# app/schemas/heroes_filter.py
from fastapi_filter.contrib.sqlalchemy import Filter
from app.models.heroes import Hero
from pydantic import Field


class HeroFilter(Filter):
    search: str | None = Field(None, description="按 name/alias/powers 模糊搜索")
    order_by: list[str] = Field(
        [],
        description="排序字段，如 -name,powers",
        json_schema_extra={"example": [["-name", "powers"]]},
    )    

    # 自定义排序实现
    def sort(self, query):
        # 让 fastapi-filter 先处理前端给的 order_by
        if self.ordering_values:
            query = super().sort(query)

        # 追加默认/固定排序
        if not any(v.lstrip("+-") == "name" for v in self.ordering_values):
            query = query.order_by(Hero.name.asc())
        query = query.order_by(Hero.id.asc())

        return query

    class Constants(Filter.Constants):
        model = Hero
         # 使用自定义字段名称，默认为 `order_by`和`search`
         # 如果要自定义字段名称，可以在这里指定，但上面的字段也要改
        # ordering_field_name = "sorting" 
        # search_field_name = "find"
        search_model_fields = ["name", "alias", "powers"] # 指定搜索字段，必须，否则搜索不起作用，会报错
