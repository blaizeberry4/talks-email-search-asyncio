from aiohttp import web
from functools import partial

from ml import nn_lookup, semantic_search

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
async def sem_search(request):
    body = await request.json()

    # Semantic search is a costly CPU task, so run it asynchronously
    # in a process pool executor (pool of separate CPUs so we don't block
    # the event loop and can process multiple requests concurrently)
    neighbors, distances = await request.app.loop.run_in_executor(
        request.app.process_executor,
        # AbstractEventLoop.run_in_executor does not allow for a function
        # call with arguments natively so bind arguments to the function
        # using functools.partial
        partial(semantic_search, body.get("query"))
    )
    neighbors = neighbors.tolist()

    results = await request.app.mongodb.emaildump.find({
        "email_counter": {
            "$in": neighbors
        }
    }).to_list(length=len(neighbors))

    return web.json_response(results)

@routes.get("/search/similar")
async def sim_search(request):
    nn_index = int(request.rel_url.query['nn_index'])
    # TODO - only select the vector
    vector = await request.app.mongodb.emaildump.find_one({
        "email_counter": nn_index
    }, {"topic_vector": 1}) 
    
    # Nearest neighbors is a costly CPU task, so run it asynchronously
    # in a process pool executor (pool of separate CPUs so we don't block
    # the event loop and can process multiple requests concurrently)
    neighbors, distances = await request.app.loop.run_in_executor(
        request.app.process_executor,
        # AbstractEventLoop.run_in_executor does not allow for a function
        # call with arguments natively so bind arguments to the function
        # using functools.partial
        partial(nn_lookup, vector["topic_vector"])
    )
    neighbors = neighbors.tolist()

    results = await request.app.mongodb.emaildump.find({
        "email_counter": {
            "$in": neighbors
        }
    }).to_list(length=len(neighbors))

    return web.json_response(results)

