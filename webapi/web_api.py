import requests
import json


class WebAPI():
    """
    General class for interacting with web APIs
    """

    def __init__(self, api_key: str, base_url: str, headers: dict) -> None:
        self.api_key = api_key
        self._base_url = base_url
        self._headers = headers

    def _get_url(self, query: str) -> dict:
        """
        Downloads the URL and returns the result as a dict
        param:
            query: str - the query to be appended to the base URL
        """
        response = requests.get(query, headers=self._headers)
        json_data = response.json()
        return json_data
