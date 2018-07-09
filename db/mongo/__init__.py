import asyncio
import motor.motor_asyncio

import settings


async def setup_mongo_interface(app):
    await asyncio.sleep(0)
    mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.db.MONGO_CXN_STR)
    setattr(app, "mongodb_client", mongo_client)
    setattr(app, "mongodb", mongo_client[settings.db.MONGO_DB_NAME])

async def close_mongo_interface(app):
    await app.mongodb_client.close()
