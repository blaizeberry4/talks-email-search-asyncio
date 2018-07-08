import os

DEFAULT_NUMBER_NEIGHBORS = int(os.getenv("DEFAULT_NUMBER_NEIGHBORS"))
LDA_MODEL_PATH = os.getenv("LDA_MODEL_PATH")
LDA_DICTIONARY_PATH = os.getenv("LDA_DICTIONARY_PATH")
NN_INDEX_PATH = os.getenv("NN_INDEX_PATH")

for setting in [
    DEFAULT_NUMBER_NEIGHBORS,
    LDA_MODEL_PATH,
    LDA_DICTIONARY_PATH,
    NN_INDEX_PATH
]:
    if not setting:
        raise EnvironmentError("Missing environment variable!")