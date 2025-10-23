#!/usr/bin/env python3

import io
import csv
import logging
from typing import Optional

from binary_reader import BinReader
from config import Config
from helpers import platform_name, decode_seed_key, format_generation_capacity
from models import PlayerData
from utils import generate_random_steam_user_id, http_get

logger = logging.getLogger(__name__)


class UserDataDownloader:
    """Handles downloading and parsing DSP Milky Way user data."""

    def __init__(self, config: Optional[Config] = None, platform: int = 1, user_id: Optional[int] = None):
        """
        Initialize the user data downloader.

        Args:
            config: Configuration object (optional)
            platform: Platform ID (1=Steam, 2=WeGame, 3=XGP, 0=Standalone)
            user_id: User ID to use (optional, generates random if not provided)
        """
        self.config = config or Config()
        self.user_id = user_id if user_id is not None else generate_random_steam_user_id()
        self.platform = platform

    def download_and_parse_user_data(self) -> list[PlayerData]:
        """
        Download and parse all user data from the server.

        Returns:
            List of PlayerData objects

        Raises:
            RuntimeError: If download or parsing fails
        """
        try:
            # Build the user data URL
            url = self.config.get_all_user_data_url(self.user_id, self.platform)
            logger.info(f"Fetching user data from: {url}")

            # Download the raw binary data
            data = http_get(url)
            logger.info(f"Downloaded {len(data)} bytes of user data")

            # Parse the binary data
            players = self._parse_user_data(data)
            logger.info(f"Successfully parsed {len(players)} player records")

            # Save to CSV file
            self._save_user_data_csv(players)
            logger.info(f"User data saved to: {self.config.user_data_csv}")

            return players

        except Exception as e:
            logger.error(f"Failed to download and parse user data: {e}")
            raise RuntimeError(f"Failed to download and parse user data: {e}") from e

    def _parse_user_data(self, data: bytes) -> list[PlayerData]:
        """
        Parse the binary user data.

        Args:
            data: Raw binary data from the server

        Returns:
            List of PlayerData objects

        The binary format matches the C# implementation:
        - Int32: version/header (unused)
        - Int32: number of player records
        - For each player:
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
            header = r.i32()
            logger.info(f"Header/Version: {header}")

            # Read number of players
            num_players = r.i32()
            logger.info(f"Parsing {num_players} player records")

            for _ in range(num_players):
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

        return players

    def _save_user_data_csv(self, players: list[PlayerData]) -> None:
        """
        Save user data to CSV file.

        Args:
            players: List of PlayerData objects to save
        """
        self.config.ensure_output_dir()

        with open(self.config.user_data_csv, "w", newline="", encoding="utf-8") as f:
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
