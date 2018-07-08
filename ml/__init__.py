from azure.storage.blob import BlockBlobService
from concurrent.futures import ProcessPoolExecutor
from gensim.corpora import Dictionary
from gensim.models import ldamodel
from multiprocessing import cpu_count
import nmslib
import numpy as np

import settings

# Constants
DEFAULT_NUMBER_NEIGHBORS = settings.ml.DEFAULT_NUMBER_NEIGHBORS

# Read configuration from environment
blob_service = BlockBlobService(connection_string=settings.db.BLOB_STORAGE_CONNECTION_STRING)
blob_service_container = settings.db.BLOB_STORAGE_CONTAINER
lda_model_path = settings.ml.LDA_MODEL_PATH
lda_dictionary_path = settings.ml.LDA_DICTIONARY_PATH
nn_index_path = settings.ml.NN_INDEX_PATH

# Pull LDA and HNSW model artifacts from Blob Storage
blob_service.get_blob_to_path(blob_service_container, lda_model_path, lda_model_path)
blob_service.get_blob_to_path(blob_service_container, lda_dictionary_path, lda_dictionary_path)
blob_service.get_blob_to_path(blob_service_container, nn_index_path, nn_index_path)

# Instantiate models
lda_model = ldamodel.LdaModel.load(lda_model_path)
lda_dictionary = Dictionary().load(lda_dictionary_path)
nn_index = nmslib.init(method = 'hnsw', space = 'cosinesimil').loadIndex(nn_index_path)


def setup_ml_process_pool(app):
    # Leave a CPU for the server to run on
    setattr(app, 'process_executor', ProcessPoolExecutor(max_workers=cpu_count() - 1))

def semantic_search(query):
    docs_bow = lda_dictionary.doc2bow(query.split())
    doc_vector = lda_model[docs_bow]
    
    return nn_lookup(doc_vector)

def nn_lookup(doc_vector, n=DEFAULT_NUMBER_NEIGHBORS):
    return nn_index.knnQuery(doc_vector, n)
