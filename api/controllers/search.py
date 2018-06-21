from aiohttp import web
import functools.partial

import ml.semantic_search
import ml.nn_lookup

routes = web.RouteTableDef()

@routes.post("/search/keyword")
async def keyword_search(request):
    body = await request.json()

    results = await request.app.search.execute({
        "search": body.get("query"),
        "filter": body.get("filter"),
        "skip": body.get("skip"),
        "top": body.get("top"),
        "queryType": "full",
        "select": body.get("fields"),
        "count": True
    })

    return web.json_response(results)

@routes.post("/search/semantic")
async def semantic_search(request):
    body = await request.json()

    # Semantic search is a costly CPU task, so run it asynchronously
    # in a process pool executor (pool of separate CPUs so we don't block
    # the event loop and can process multiple requests concurrently)
    neighbors = await request.app.loop.run_in_executor(
        request.app.process_executor,
        # AbstractEventLoop.run_in_executor does not allow for a function
        # call with arguments natively so bind arguments to the function
        # using functools.partial
        functools.partial(ml.semantic_search, body.get("query"))
    )

    results = await request.app.mongo.email.find({
        "nn_index": {
            "$in": neighbors
        }
    })

    return web.json_response(results)

@routes.get("/search/similar")
async def similar_search(request):
    nn_index = request.rel_url.query['nn_index']
    
    # Nearest neighbors is a costly CPU task, so run it asynchronously
    # in a process pool executor (pool of separate CPUs so we don't block
    # the event loop and can process multiple requests concurrently)
    neighbors = await request.app.loop.run_in_executor(
        request.app.process_executor,
        # AbstractEventLoop.run_in_executor does not allow for a function
        # call with arguments natively so bind arguments to the function
        # using functools.partial
        functools.partial(ml.nn_lookup, nn_index)
    )

    results = await request.app.mongo.email.find({
        "nn_index": {
            "$in": neighbors
        }
    })

    return web.json_response(results)

