from concurrent.futures import ProcessPoolExecutor
from multiprocessing import cpu_count

def setup_ml_process_pool(app):
    # Leave a CPU for the server to run on
    setattr(app, 'process_executor', ProcessPoolExecutor(max_workers=cpu_count() - 1))