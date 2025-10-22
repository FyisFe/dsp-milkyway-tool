#!/usr/bin/env python3

import io
import os
from utils import generate_random_steam_user_id, login, fetch_full_data
import gzip

class FullDataDownloader:
    def __init__(self):
        self.user_id = generate_random_steam_user_id()
        
    def login(self) -> str:
        try:
            response = login(self.user_id)
            if len(response.split(",")) != 2:
                raise ValueError("Invalid login response format. Expected '<login_key>,<full_data_url>'.")
            self.login_key, self.full_data_url = response.split(",")
        except Exception as e:
            raise RuntimeError(f"Login failed: {e}")            
    
    def download_full_data(self) -> bytes:
        try:
            # Create output directory if it doesn't exist
            os.makedirs("output", exist_ok=True)

            full_data = fetch_full_data(self.full_data_url)
            with gzip.GzipFile(fileobj=io.BytesIO(full_data)) as gzf, open(f"output/{self.full_data_url.split('/')[-1]}", "wb") as f:
                chunk = gzf.read()
                f.write(chunk)

        except Exception as e:
            raise RuntimeError(f"Failed to download full data: {e}")

if __name__ == "__main__":
    downloader = FullDataDownloader()
    login_data = downloader.login()
    print(f"Logged in with user ID: {downloader.user_id}")
    print(f"login_key: {downloader.login_key}")
    print(f"full_data_url: {downloader.full_data_url}")
    
    full_data = downloader.download_full_data()
