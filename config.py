#!/usr/bin/env python3

import os
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""

    server_address: str = "http://8.140.162.132/"
    login_header_api: str = "login/header"
    download_full_data_api: str = "download"
    get_statistic_api: str = "query/statisticdata"
    get_all_user_data_api: str = "query/alluserdata"
    output_dir: str = "output"

    @property
    def top_ten_csv(self) -> str:
        """Get path for top ten CSV file in output directory."""
        return os.path.join(self.output_dir, "top_ten.csv")

    @property
    def summary_txt(self) -> str:
        """Get path for summary text file in output directory."""
        return os.path.join(self.output_dir, "summary.txt")

    @property
    def all_csv(self) -> str:
        """Get path for all seeds CSV file in output directory."""
        return os.path.join(self.output_dir, "all.csv")

    @property
    def statistics_txt(self) -> str:
        """Get path for statistics text file in output directory."""
        return os.path.join(self.output_dir, "statistics.txt")

    @property
    def user_data_csv(self) -> str:
        """Get path for user data CSV file in output directory."""
        return os.path.join(self.output_dir, "user_data.csv")

    def get_login_url(self, user_id: int) -> str:
        """Get the login URL with user ID."""
        return f"{self.server_address}{self.login_header_api}?user_id={user_id}"

    def get_download_url(self, full_data_url: str) -> str:
        """Get the download URL for full data."""
        return f"{self.server_address}{self.download_full_data_api}/{full_data_url}"

    def get_statistic_url(self, user_id: int, platform: int) -> str:
        """Get the statistics URL with user ID and platform."""
        return f"{self.server_address}{self.get_statistic_api}?user_id={user_id}&platform={platform}"

    def get_all_user_data_url(self, user_id: int, platform: int) -> str:
        """Get the all user data URL with user ID and platform."""
        return f"{self.server_address}{self.get_all_user_data_api}?user_id={user_id}&platform={platform}"

    def ensure_output_dir(self) -> None:
        """Create output directory if it doesn't exist."""
        os.makedirs(self.output_dir, exist_ok=True)
