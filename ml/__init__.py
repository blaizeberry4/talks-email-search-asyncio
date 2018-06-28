from concurrent.futures import ProcessPoolExecutor
from gensim.corpora import Dictionary
from gensim.models import ldamodel
from multiprocessing import cpu_count
import nmslib as nms
import numpy as np
from pymongo import MongoClient

def setup_ml_process_pool(app):
    # Leave a CPU for the server to run on
    setattr(app, 'process_executor', ProcessPoolExecutor(max_workers=cpu_count() - 1))


client = MongoClient()

"""
NEED TO REMOVE FILEPATHS AND PULL FROM BLOB STORAGE
"""
lda_model = ldamodel.LdaModel.load('lda_filepath') 
dictionary = Dictionary().load('dict_filepath')
index = nms.init(method = 'hnsw', space = 'cosinesimil')
index.loadIndex('index_filepath')
emailCol = client['EnronEmailData'].emails
topicCol = client['DocTopicVectors'].tVectors

def semantic_search(*words):
    words = words.split()
    docs_bow = dictionary.doc2bow(words)
    docs_topic_distribution = lda_model[docs_bow]
    
    results, distances = nn_lookup_vector(docs_topic_distribution)
    return results

def nn_lookup(doc_topic_vector):
    nearest_n, distances = index.knnQuery(doc_topic_vector, 20)
    result = []
    for unique_number in nearest_n:
        # this is why documents must be sorted when adding them to the index!!
        result_email = topicCol.find_one({'doc_counter': np.asscalar(unique_number)})
        result.append(result_email['_id'])
    return result, distances
