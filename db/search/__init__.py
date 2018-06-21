import asyncio
from aiohttp import ClientSession

import settings
from interfaces import *

async def setup_search_interface(app):
    await asyncio.sleep(0)

    setattr(app, 'search', AzureSearchInterface(
        emails=AzureSearchIndexInterface(
            settings.db.AZURE_SEARCH_EMAILS_INDEX_URL,
            settings.db.AZURE_SEARCH_API_KEY,
            ClientSession(loop=app.loop)
        )
    ))