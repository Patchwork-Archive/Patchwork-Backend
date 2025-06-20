# Allows you to pull storage statistics from SQL db
from webapi.storage_api import StorageAPI
from database.sql_handler import SQLHandler

class ManualStorageAPI(StorageAPI):
    def __init__(self, server: SQLHandler) -> None:
        super().__init__(None, None, None) # Since we only need to pull from DB
        self.server = server

    def get_storage_used(self) -> tuple[int,str]:
        """
        Returns the amount of storage used and the unit of measurement
        """
        print("Getting storage used")
        if not self.server.check_row_exists("kv", "DATA", "video_bucket_size"):
            self.server.insert_row("kv", "DATA, REFERENCE", ("video_bucket_size", "0"))
        print(self.server.get_query_result("SELECT REFERENCE FROM kv WHERE DATA = 'video_bucket_size'"))
        storage_used = int(self.server.get_query_result("SELECT REFERENCE FROM kv WHERE DATA = 'video_bucket_size'")[0][0])
        units = self.server.get_query_result("SELECT REFERENCE FROM kv WHERE DATA = 'video_bucket_size_units'")[0][0]
        return storage_used, units

    def get_number_of_files(self) -> int:
        """
        Returns the number of files stored
        """
        if not self.server.check_row_exists("kv", "DATA", "video_bucket_count"):
            self.server.insert_row("kv", "DATA, REFERENCE", ("video_bucket_count", "0"))
        obj_count = int(self.server.get_query_result("SELECT REFERENCE FROM kv WHERE DATA = 'video_bucket_count'")[0][0])
        print(obj_count)
        return obj_count
