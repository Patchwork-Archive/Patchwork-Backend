from webapi.web_api import WebAPI
from abc import ABC

class StorageAPI(ABC, WebAPI):
    """
    The data for this use case is stored on CloudFlare R2 Storage
    However so long as all methods are implemented the class can be re-written to use any other API
    """
    def __init__(self, api_key: str, base_url: str, headers:dict) -> None:
        super().__init__(api_key, base_url, headers)

    def get_storage_used(self) -> tuple[int,str]:
        """
        Returns the amount of storage used and the unit of measurement
        """
        pass

    def get_number_of_files(self) -> int:
        """
        Returns the number of files stored
        """
        pass
