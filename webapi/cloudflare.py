from webapi.storage_api import StorageAPI
from datetime import datetime, timedelta

class CloudflareAPI(StorageAPI):
    """
    The data for this use case is stored on CloudFlare R2 Storage
    However so long as all methods are implemented the class can be re-written to use any other API
    """
    def __init__(self, api_key: str, account_id: str, bucket_name: str, base_url: str = "https://api.cloudflare.com/client/v4", _refresh_interval_min: int = 15) -> None:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        super().__init__(api_key, base_url, headers)
        self._account_id = account_id
        self.bucket_name = bucket_name
        self._refresh_interval_min = _refresh_interval_min
        self._buffer = {}
    
    def _save_result_to_buffer(self, key: str, value, timestamp: datetime) -> None:
        """
        Saves the results of a qeury to a buffer to reduce the number of API calls 
        """
        self._buffer[key] = {"value": value, "timestamp": timestamp}
    
    def _update_storage_statistics(self) -> None:
        storage_data = self._get_url(f"{self._base_url}/accounts/{self._account_id}/r2/buckets/{self.bucket_name}/usage")
        result = storage_data['result']
        for key in result:
            self._save_result_to_buffer(key, result[key], datetime.now())
    
    def get_storage_used(self) -> tuple[int,str]:
        """
        Returns the amount of storage used in bytes
        """
        if "payloadSize" not in self._buffer or self._buffer["payloadSize"]["timestamp"] < datetime.now() - timedelta(minutes=self._refresh_interval_min):
            self._update_storage_statistics()
        return self._buffer["payloadSize"]["value"]

    def get_number_of_files(self) -> int:
        """
        Returns the number of files stored
        """
        if "objectCount" not in self._buffer or self._buffer["objectCount"]["timestamp"] < datetime.now() - timedelta(minutes=self._refresh_interval_min):
            self._update_storage_statistics()
        return self._buffer["objectCount"]["value"]
            
