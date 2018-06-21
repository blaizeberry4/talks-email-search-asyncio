class AzureSearchIndexInterface:
    def __init__(self, url, api_key, session):
        self.url, self.api_key, self.session = url, api_key, session

    async def execute(self, query):
        raw = await self.session.post(
            url=self.url,
            json=query,
            headers={ "api-key": self.api_key }
        )

        response = await raw.json()

        return self._map_response_to_results(response)

    @staticmethod
    def _map_response_to_results(response):
        return {
            "count": response["@odata.count"],
            "emails": response["value"]
        }

    async def close(self):
        await self.session.close()
    

class AzureSearchInterface:
    def __init__(self, **kwargs):
        for index_name, index_interface in kwargs.items():
            setattr(self, index_name, index_interface)