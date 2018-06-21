import asyncio
import motor.motor_asyncio

import settings

mongo_client = motor.motor_asyncio.AsyncIOMotorClient(settings.db.MONGO_CXN_STR)

async def setup_mongo_interface(app):
    await asyncio.sleep(0)
    setattr(app, 'mongodb_client', app.mongo_client)
    setattr(app, 'mongodb', app.mongo_client[settings.db.MONGO_DB_NAME])

async def close_mongo_interface(app):
    await app.mongo_client.close()