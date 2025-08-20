# /scripts/fill_fake_heroes.py
import asyncio

from app.models import Hero
from app.core.database import setup_database_connection, get_session_factory, close_database_connection



# 2. 假数据池
NAMES = [
    "Peter Parker", "Tony Stark", "Steve Rogers", "Bruce Banner", "Natasha Romanoff",
    "Clark Kent", "Bruce Wayne", "Diana Prince", "Barry Allen", "Arthur Curry",
    "Reed Richards", "Sue Storm", "Johnny Storm", "Ben Grimm", "Ororo Munroe"
]
ALIASES = [
    "Spider-Man", "Iron Man", "Captain America", "Hulk", "Black Widow",
    "Superman", "Batman", "Wonder Woman", "Flash", "Aquaman",
    "Mr. Fantastic", "Invisible Woman", "Human Torch", "The Thing", "Storm"
]
POWERS = [
    "Wall-crawling, super strength, spider-sense",
    "Genius-level intellect, powered armor suit",
    "Peak human condition, vibranium shield mastery",
    "Limitless strength, durability increases with anger",
    "Master spy & assassin, slowed aging",
    "Flight, heat vision, invulnerability",
    "World's greatest detective, peak human conditioning",
    "Super strength, flight, lasso of truth",
    "Speed Force, time travel via running",
    "Atlantean physiology, hydrokinesis",
    "Elasticity, genius intellect",
    "Invisibility, force-field projection",
    "Pyrokinesis, flight",
    "Super strength & durability, rock-like hide",
    "Weather manipulation, flight"
]

# 3. 生成并插入
async def fill_fake_data():
    await setup_database_connection()          # 初始化全局 engine & factory
    factory = get_session_factory()
    async with factory() as session:
        
        # 1. 造数据
        heroes = [
            Hero(
                name=name,
                alias=alias,
                powers=powers
            )
            for name, alias, powers in zip(NAMES, ALIASES, POWERS)
        ]

        # 2. 提交
        session.add_all(heroes)
        await session.commit()
        print("✅ 成功插入", len(heroes), "条英雄记录")

    await close_database_connection()          # 优雅关闭

if __name__ == "__main__":
    asyncio.run(fill_fake_data())