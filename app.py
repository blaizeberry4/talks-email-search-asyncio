from aiohttp import web
import asyncio
import aiohttp_cors
from aiohttp_swagger import setup_swagger
from concurrent.futures import ProcessPoolExecutor
import logging
from multiprocessing import cpu_count
import uvloop

from api.controllers import controllers
from db.mongo import setup_mongo_interface
from db.search import setup_search_interface
from settings.logging import config as log_config
from settings.app import host, port


def setup_logging(app):
    logging.config.dictConfig(log_config)

def setup_routes(app):
    for controller in controllers:
        app.router.add_routes(controller.routes)

def setup_cors(app):
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*"
        )
    })
    
    for route in list(app.router.routes()):
        cors.add(route)

def setup_dbs(app):
    app.on_startup.append(setup_search_interface)
    app.on_startup.append(setup_mongo_interface)

def setup_process_pool(app):
    # Leave a CPU for the server to run on
    setattr(app, 'process_executor', ProcessPoolExecutor(max_workers=cpu_count() - 1))


if __name__ == "__main__":
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    app = web.Application()

    # Setup that can be done before running the app
    setup_logging(app)
    # setup_swagger(app, swagger_from_file="swagger.json")
    setup_routes(app)
    setup_cors(app)
    setup_process_pool(app)

    # Setup that needs to be deffered until app is started 
    # (to ensure an event loop singleton)
    for deferred in [setup_search_interface, setup_mongo_interface]:
        app.on_startup.append(deferred)
    
    web.run_app(app, host=host, port=port)
