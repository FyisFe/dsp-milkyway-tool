#!/usr/bin/env python3

import io
import csv
import logging
import time
from typing import Optional

from binary_reader import BinReader
from config import Config
from helpers import platform_name, decode_seed_key, format_generation_capacity, encode_seed_key
from models import PlayerData
from utils import generate_random_steam_user_id, http_get

logger = logging.getLogger(__name__)


class ClusterPlayerDownloader:
    """Handles downloading and parsing DSP Milky Way cluster player data by seed."""

    def __init__(self, config: Optional[Config] = None, platform: int = 1, user_id: Optional[int] = None):
        """
        Initialize the cluster player downloader.

        Args:
            config: Configuration object (optional)
            platform: Platform ID (1=Steam, 2=WeGame, 3=XGP, 0=Standalone)
            user_id: User ID to use (optional, generates random if not provided)
        """
        self.config = config or Config()
        self.user_id = user_id if user_id is not None else generate_random_steam_user_id()
        self.platform = platform

    def download_and_parse_cluster_players(
        self,
        seed: int,
        stars: int,
        resource_mult: int,
        combat_diff: int,
        max_pages: int = 10
    ) -> list[PlayerData]:
        """
        Download and parse cluster player data for a specific seed.

        Args:
            seed: The seed number
            stars: Number of stars
            resource_mult: Resource multiplier (raw value, e.g., 10 for 1.0x)
            combat_diff: Combat difficulty (raw value, 0 for peace mode)
            max_pages: Maximum number of pages to download (default 10)

        Returns:
            List of PlayerData objects

        Raises:
            RuntimeError: If download or parsing fails
        """
        try:
            # Encode the seed key
            seed_key = encode_seed_key(seed, stars, resource_mult, combat_diff)
            logger.info(f"Encoded seed key: {seed_key} (seed={seed}, stars={stars}, res_mult={resource_mult}, combat={combat_diff})")

            all_players = []
            page_size = 10  # Fixed page size as per C# code

            for page_index in range(max_pages):
                # Wait 0.5 second before each API call
                if page_index > 0:
                    logger.info("Waiting 0.5 second before next request...")
                    time.sleep(0.5)

                logger.info(f"Fetching page {page_index}...")

                # Download page
                url = self.config.get_cluster_user_page_url(
                    seed_key, page_index, page_size, self.user_id, self.platform
                )
                logger.info(f"URL: {url}")

                data = http_get(url)
                logger.info(f"Downloaded {len(data)} bytes")

                # Parse page
                players, total_count, current_page = self._parse_cluster_page(data)

                logger.info(f"Page {current_page}: Got {len(players)} players out of {total_count} total")

                all_players.extend(players)

                # If we got fewer players than page size, we've reached the end
                if len(players) < page_size:
                    logger.info(f"Reached end of data at page {page_index}")
                    break

            logger.info(f"Successfully downloaded {len(all_players)} total player records")

            # Save to CSV
            self._save_cluster_players_csv(all_players, seed, stars, resource_mult, combat_diff)
            logger.info(f"Cluster players saved to: {self.config.cluster_players_csv}")

            return all_players

        except Exception as e:
            logger.error(f"Failed to download and parse cluster players: {e}")
            raise RuntimeError(f"Failed to download and parse cluster players: {e}") from e

    def _parse_cluster_page(self, data: bytes) -> tuple[list[PlayerData], int, int]:
        """
        Parse a single page of cluster player data.

        Args:
            data: Raw binary data from the server

        Returns:
            Tuple of (list of PlayerData, total_count, page_index)

        The binary format matches the C# implementation:
        - Int32: version/header (unused)
        - Int64: total count of players for this seed
        - Int32: current page index
        - Int32: number of records in this page
        - For each player (up to 10):
            - Int64: seedKey
            - Int64: userId
            - Byte: platform
            - String: name (using ReadString which reads 7-bit encoded length + UTF-8 bytes)
            - Int64: genCap
            - Byte: isAnon
        """
        players = []

        with io.BytesIO(data) as stream:
            r = BinReader(stream)

            # Read header/version (unused)
            _ = r.i32()

            # Read total count
            total_count = r.i64()

            # Read current page index
            page_index = r.i32()

            # Read number of records in this page
            num_records = r.i32()

            logger.info(f"Parsing page {page_index}: {num_records} records (total: {total_count})")

            # Read each player record (up to 10)
            for _ in range(min(num_records, 10)):
                seed_key = r.i64()
                user_id = r.i64()
                platform = r.u8()

                # ReadString in C# BinaryReader: reads 7-bit encoded length, then UTF-8 bytes
                name_len = r.read7bit_encoded_int()
                name_bytes = r.read(name_len)
                name = name_bytes.decode("utf-8", errors="replace")

                gen_cap = r.i64()
                is_anon = r.u8()

                # Decode seed key
                seed, stars, res_mult, combat = decode_seed_key(seed_key)

                player = PlayerData(
                    seed=seed,
                    stars=stars,
                    resource_multiplier=res_mult,
                    combat_difficulty=combat,
                    user_id=user_id,
                    platform=platform_name(platform),
                    account_name=name,
                    generation_capacity=format_generation_capacity(gen_cap * 60),
                    is_anonymous=is_anon > 0,
                )
                players.append(player)

        return players, total_count, page_index

    def _save_cluster_players_csv(
        self,
        players: list[PlayerData],
        seed: int,  # noqa: ARG002
        stars: int,  # noqa: ARG002
        resource_mult: int,  # noqa: ARG002
        combat_diff: int  # noqa: ARG002
    ) -> None:
        """
        Save cluster player data to CSV file.

        Args:
            players: List of PlayerData objects to save
            seed: The seed number
            stars: Number of stars
            resource_mult: Resource multiplier
            combat_diff: Combat difficulty
        """
        self.config.ensure_output_dir()

        with open(self.config.cluster_players_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            # Write header with Chinese labels
            w.writerow(
                ["种子", "星数", "资源倍率", "战斗难度", "用户ID", "平台", "账号", "发电量", "匿名"]
            )

            # Write player data
            for player in players:
                w.writerow(
                    [
                        str(player.seed),
                        str(player.stars),
                        player.resource_multiplier,
                        player.combat_difficulty,
                        str(player.user_id),
                        player.platform,
                        player.account_name,
                        player.generation_capacity,
                        str(player.is_anonymous),
                    ]
                )
