from aiohttp import web
from functools import partial

from ml import nn_lookup, semantic_search

routes = web.RouteTableDef()

@routes.post("/search/keyword")
async def keyword_search(request):
    body = await request.json()

    results = await request.app.search.emails.execute({
        "search": body.get("query"),
        "skip": body.get("skip"),
        "top": body.get("top"),
        "count": True
    })

    return web.json_response(results["emails"])

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
    }, {
        "content": 1,
        "sender": 1,
        "recipient": 1,
        "date": 1,
        "subject": 1,
        "email_counter": 1
    }).to_list(length=len(neighbors))
    sorted_results = []
    results_dict = { v["email_counter"]: v for v in results }
    for idx in neighbors:
        sorted_results.append(results_dict[idx])

    return web.json_response(sorted_results)

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
    }, {
        "content": 1,
        "sender": 1,
        "recipient": 1,
        "date": 1,
        "subject": 1,
        "email_counter": 1
    }).to_list(length=len(neighbors))
    sorted_results = []
    results_dict = { v["email_counter"]: v for v in results }
    for idx in neighbors:
        sorted_results.append(results_dict[idx])

    return web.json_response(sorted_results)

