#!/usr/bin/env python3

import io
import os
import csv
import gzip
import logging
from typing import Optional

from binary_reader import BinReader
from config import Config
from helpers import platform_name, decode_seed_key, format_generation_capacity
from models import PlayerData, SeedData, Summary
from utils import generate_random_steam_user_id, login, fetch_full_data

logger = logging.getLogger(__name__)


class FullDataDownloader:
    """Handles downloading and parsing DSP Milky Way full data."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.user_id = generate_random_steam_user_id()
        self.login_key: Optional[str] = None
        self.full_data_url: Optional[str] = None

    def login(self) -> None:
        """
        Log in to the server and retrieve login credentials.

        Raises:
            ValueError: If the login response format is invalid
            RuntimeError: If login fails
        """
        try:
            response = login(self.user_id)
            if len(response.split(",")) != 2:
                raise ValueError(
                    "Invalid login response format. Expected '<login_key>,<full_data_url>'."
                )
            self.login_key, self.full_data_url = response.split(",")
            logger.info(f"Successfully logged in with user ID: {self.user_id}")
        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise RuntimeError(f"Login failed: {e}") from e

    def download_full_data(self) -> str:
        """
        Download and decompress full data from the server.

        Returns:
            Path to the downloaded file

        Raises:
            RuntimeError: If download fails
            ValueError: If not logged in
        """
        if not self.full_data_url:
            raise ValueError("Must login before downloading full data")

        try:
            # Create output directory if it doesn't exist
            self.config.ensure_output_dir()

            full_data = fetch_full_data(self.full_data_url)
            filename = os.path.join(
                self.config.output_dir, self.full_data_url.split("/")[-1]
            )

            with gzip.GzipFile(fileobj=io.BytesIO(full_data)) as gzf, open(
                filename, "wb"
            ) as f:
                chunk = gzf.read()
                f.write(chunk)

            logger.info(f"Full data downloaded and saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to download full data: {e}")
            raise RuntimeError(f"Failed to download full data: {e}") from e

    def parse_full_data(self, filename: str) -> None:
        """
        Parse the downloaded full data file.

        Args:
            filename: Path to the binary data file to parse

        Raises:
            FileNotFoundError: If the file doesn't exist
            RuntimeError: If parsing fails
        """
        try:
            with open(filename, "rb") as f:
                r = BinReader(f)
                _ = r.u32()  # header version (unused)
                self._load_top_ten_player_data(r)
                self._load_other_data(r)
            logger.info("Successfully parsed full data")
        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse full data: {e}")
            raise RuntimeError(f"Failed to parse full data: {e}") from e

    def _load_top_ten_player_data(self, r: BinReader) -> None:
        """
        Load and save top ten player data to CSV.

        Args:
            r: Binary reader instance
        """
        _ = r.u32()  # block tag / version (unused)
        num = r.i32()

        players = []
        for _ in range(num):
            seed_key = r.i64()
            user_id = r.i64()
            platform = r.u8()

            name_len = r.read7bit_encoded_int()
            name_bytes = r.read(name_len)
            name = name_bytes.decode("utf-8", errors="replace")

            gen_cap = r.i64()
            is_anon = r.u8()

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

        self._save_top_ten_csv(players)
        logger.info(f"Loaded {len(players)} top ten player records")

    def _save_top_ten_csv(self, players: list[PlayerData]) -> None:
        """Save top ten player data to CSV file."""
        with open(self.config.top_ten_csv, "w", newline="", encoding="utf-8") as of:
            w = csv.writer(of)
            w.writerow(
                ["种子", "星数", "资源倍率", "战斗难度", "用户ID", "平台", "账号", "发电量", "匿名"]
            )

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

    def _load_other_data(self, r: BinReader) -> None:
        """
        Load summary and aggregated seed data.

        Args:
            r: Binary reader instance
        """
        # Summary block
        _ = r.u32()  # version (unused)
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

        self._save_summary(summary)
        logger.info(f"Loaded summary: {total_player} players, {total_dyson_sphere} dyson spheres")

        # Aggregated per-seed block
        _ = r.u32()  # version (unused)
        num = r.i32()

        seeds = []
        for _ in range(num):
            seed_key = r.i64()
            gen_cap = r.f32()
            player_num = r.i32()

            seed, stars, res_mult, combat = decode_seed_key(seed_key)

            seed_data = SeedData(
                seed=seed,
                stars=stars,
                resource_multiplier=res_mult,
                combat_difficulty=combat,
                player_count=player_num,
                total_generation_capacity=format_generation_capacity(int(gen_cap * 60)),
            )
            seeds.append(seed_data)

            # The Go code reads an extra uint32 after each entry
            _ = r.u32()

        self._save_all_csv(seeds)
        logger.info(f"Loaded {len(seeds)} seed records")

    def _save_summary(self, summary: Summary) -> None:
        """Save summary statistics to text file."""
        with open(self.config.summary_txt, "w", encoding="utf-8") as of:
            of.write(
                f"总玩家数: {summary.total_players}\n"
                f"总发电量: {summary.total_generation_capacity}\n"
                f"总太阳帆数: {summary.total_sails_launched}\n"
                f"总戴森球数: {summary.total_dyson_spheres}\n"
            )

    def _save_all_csv(self, seeds: list[SeedData]) -> None:
        """Save aggregated seed data to CSV file."""
        with open(self.config.all_csv, "w", newline="", encoding="utf-8") as of:
            w = csv.writer(of)
            w.writerow(["种子", "星数", "资源倍率", "战斗难度", "用户数", "总发电量"])

            for seed in seeds:
                w.writerow(
                    [
                        str(seed.seed),
                        str(seed.stars),
                        seed.resource_multiplier,
                        seed.combat_difficulty,
                        str(seed.player_count),
                        seed.total_generation_capacity,
                    ]
                )
