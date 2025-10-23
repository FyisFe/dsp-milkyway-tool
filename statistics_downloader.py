#!/usr/bin/env python3

import io
import logging
from typing import Optional

from binary_reader import BinReader
from config import Config
from helpers import format_generation_capacity
from models import Summary
from utils import generate_random_steam_user_id, http_get

logger = logging.getLogger(__name__)


class StatisticsDownloader:
    """Handles downloading and parsing DSP Milky Way statistics data."""

    def __init__(self, config: Optional[Config] = None, platform: int = 1):
        """
        Initialize the statistics downloader.

        Args:
            config: Configuration object (optional)
            platform: Platform ID (1=Steam, 2=WeGame, 3=XGP, 0=Standalone)
        """
        self.config = config or Config()
        self.user_id = generate_random_steam_user_id()
        self.platform = platform

    def download_and_parse_statistics(self) -> Summary:
        """
        Download and parse statistics data from the server.

        Returns:
            Summary object containing the statistics

        Raises:
            RuntimeError: If download or parsing fails
        """
        try:
            # Build the statistics URL
            url = self.config.get_statistic_url(self.user_id, self.platform)
            logger.info(f"Fetching statistics from: {url}")

            # Download the raw binary data
            data = http_get(url)
            logger.info(f"Downloaded {len(data)} bytes of statistics data")

            # Parse the binary data
            summary = self._parse_statistics_data(data)
            logger.info("Successfully parsed statistics data")

            # Save to file
            self._save_statistics(summary)
            logger.info(f"Statistics saved to: {self.config.statistics_txt}")

            return summary

        except Exception as e:
            logger.error(f"Failed to download and parse statistics: {e}")
            raise RuntimeError(f"Failed to download and parse statistics: {e}") from e

    def _parse_statistics_data(self, data: bytes) -> Summary:
        """
        Parse the binary statistics data.

        Args:
            data: Raw binary data from the server

        Returns:
            Summary object with parsed statistics

        The binary format matches the C# implementation:
        - Int32: version/header (unused)
        - Int64: total generation capacity
        - Int64: total sails launched
        - Int32: total players
        - Int32: total dyson spheres
        """
        with io.BytesIO(data) as stream:
            r = BinReader(stream)

            # Read header/version (unused in C# code)
            _ = r.i32()

            # Read statistics data
            total_gen_cap = r.i64()
            total_sail_launched = r.i64()
            total_player = r.i32()
            total_dyson_sphere = r.i32()

            summary = Summary(
                total_players=total_player,
                total_generation_capacity=format_generation_capacity(total_gen_cap * 60),
                total_sails_launched=total_sail_launched,
                total_dyson_spheres=total_dyson_sphere,
            )

            logger.info(
                f"Statistics: {total_player} players, "
                f"{total_dyson_sphere} dyson spheres, "
                f"{total_sail_launched} sails"
            )

            return summary

    def _save_statistics(self, summary: Summary) -> None:
        """
        Save statistics to text file.

        Args:
            summary: Summary object to save
        """
        self.config.ensure_output_dir()

        with open(self.config.statistics_txt, "w", encoding="utf-8") as f:
            f.write(
                f"总玩家数: {summary.total_players}\n"
                f"总发电量: {summary.total_generation_capacity}\n"
                f"总太阳帆数: {summary.total_sails_launched}\n"
                f"总戴森球数: {summary.total_dyson_spheres}\n"
            )
