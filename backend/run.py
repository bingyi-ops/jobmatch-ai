"""Entry point: init DB + seed data + start server."""
import asyncio
import os
import sys
import uvicorn

sys.path.insert(0, os.path.dirname(__file__))

from app.database import database


async def init_db():
    await database.connect()
    schema_path = os.path.join(os.path.dirname(__file__), "..", "data", "schema.sql")
    with open(schema_path, "r") as f:
        sql = f.read()
    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            await database.execute(stmt)
    await database.disconnect()
    print("✅ Database initialized")


if __name__ == "__main__":
    asyncio.run(init_db())

    # Seed if no jobs exist
    import subprocess
    result = subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "seed_data.py")])
    if result.returncode == 0:
        print("✅ Seed complete")
    else:
        print("⚠️  Seed may have failed, check above output")

    print("\n🚀 Starting JobMatch AI Server at http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs\n")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
