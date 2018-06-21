import os

AZURE_SEARCH_EMAILS_INDEX_URL = os.getenv('AZURE_SEARCH_EMAILS_INDEX_URL')
AZURE_SEARCH_API_KEY = os.getenv('AZURE_SEARCH_API_KEY')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
MONGO_CXN_STR = os.getenv('MONGO_CXN_STR')

for setting in [
    AZURE_SEARCH_EMAILS_INDEX_URL,
    AZURE_SEARCH_API_KEY,
    MONGO_DB_NAME,
    MONGO_CXN_STR
]:
    if not setting:
        raise EnvironmentError("Missing environment variable!")