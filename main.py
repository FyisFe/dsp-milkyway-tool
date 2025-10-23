#!/usr/bin/env python3

import logging
import sys

from downloader import FullDataDownloader
from statistics_downloader import StatisticsDownloader
from user_data_downloader import UserDataDownloader
from cluster_player_downloader import ClusterPlayerDownloader


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def download_full_data() -> None:
    """Download and parse full data."""
    logger = logging.getLogger(__name__)

    downloader = FullDataDownloader()

    # Login
    downloader.login()
    logger.info(f"Logged in with user ID: {downloader.user_id}")
    logger.info(f"Login key: {downloader.login_key}")
    logger.info(f"Full data URL: {downloader.full_data_url}")

    # Download full data
    filename = downloader.download_full_data()
    logger.info(f"Full data downloaded and saved to: {filename}")

    # Parse full data
    downloader.parse_full_data(filename)
    logger.info("Data parsing completed successfully")


def download_statistics() -> None:
    """Download and parse statistics data."""
    logger = logging.getLogger(__name__)

    downloader = StatisticsDownloader(platform=1)  # 1 = Steam
    logger.info(f"Using user ID: {downloader.user_id}")

    # Download and parse statistics
    summary = downloader.download_and_parse_statistics()
    logger.info("Statistics download completed successfully")

    # Print summary
    print("\n=== DSP Milky Way Statistics ===")
    print(f"Total Players: {summary.total_players}")
    print(f"Total Generation Capacity: {summary.total_generation_capacity}")
    print(f"Total Sails Launched: {summary.total_sails_launched}")
    print(f"Total Dyson Spheres: {summary.total_dyson_spheres}")
    print(f"\nSaved to: output/statistics.txt")


def download_user_data() -> None:
    """Download and parse all user data."""
    logger = logging.getLogger(__name__)

    # Ask for user ID
    user_id_input = input("\nEnter your user ID (press Enter to use random): ").strip()

    if user_id_input:
        try:
            user_id = int(user_id_input)
            print(f"Using provided user ID: {user_id}")
        except ValueError:
            logger.error("Invalid user ID format")
            print("Invalid user ID. Please enter a valid number.")
            return
    else:
        user_id = None
        print("Using randomly generated user ID")

    downloader = UserDataDownloader(platform=1, user_id=user_id)  # 1 = Steam
    logger.info(f"Using user ID: {downloader.user_id}")

    # Download and parse user data
    players = downloader.download_and_parse_user_data()
    logger.info("User data download completed successfully")

    # Print summary
    print("\n=== DSP Milky Way User Data ===")
    print(f"Total Records Downloaded: {len(players)}")
    print(f"\nSaved to: output/user_data.csv")


def download_cluster_players() -> None:
    """Download and parse cluster player data by seed."""
    logger = logging.getLogger(__name__)

    # Ask for seed parameters
    print("\nEnter seed parameters:")

    try:
        seed = int(input("种子 (Seed): ").strip())
        stars = int(input("星数 (Stars): ").strip())

        # Resource multiplier input
        res_mult_str = input("资源倍率 (Resource Multiplier, e.g., 1.0, 9.9 for 无限): ").strip()
        res_mult_float = float(res_mult_str)
        res_mult_raw = int(res_mult_float * 10)  # Convert 1.0 to 10, 0.5 to 5, 9.9 to 99

        # Combat difficulty input
        combat_str = input("战斗难度 (Combat Difficulty, 000 for peace, 1xx for combat <1-100>, e.g. 100 for 00, 199 for 99): ").strip()
        combat_raw = int(combat_str)

        # Max pages
        max_pages_str = input("Maximum pages to download (default 10): ").strip()
        max_pages = int(max_pages_str) if max_pages_str else 10

    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        print("Invalid input. Please enter valid numbers.")
        return

    print(f"\nSearching for players with:")
    print(f"  Seed: {seed}")
    print(f"  Stars: {stars}")
    print(f"  Resource Multiplier: {res_mult_float}x (raw: {res_mult_raw})")
    print(f"  Combat Difficulty: {combat_raw}")

    downloader = ClusterPlayerDownloader(platform=1)  # 1 = Steam
    logger.info(f"Using user ID: {downloader.user_id}")

    # Download and parse cluster player data
    players = downloader.download_and_parse_cluster_players(
        seed, stars, res_mult_raw, combat_raw, max_pages
    )
    logger.info("Cluster player download completed successfully")

    # Print summary
    print("\n=== DSP Milky Way Cluster Players ===")
    print(f"Total Records Downloaded: {len(players)}")
    print(f"\nSaved to: output/cluster_players.csv")


def main() -> None:
    """Main entry point for the DSP Milky Way data downloader."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Display menu and prompt for input
    print("\n=== DSP Milky Way Data Downloader ===")
    print("1. Download statistics data")
    print("2. Download full data")
    print("3. Download all user data")
    print("4. Download cluster players by seed")
    print("0. Exit")

    choice = input("\nEnter your choice (0-4): ").strip()

    if choice == "1":
        try:
            download_statistics()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
    elif choice == "2":
        try:
            download_full_data()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
    elif choice == "3":
        try:
            download_user_data()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
    elif choice == "4":
        try:
            download_cluster_players()
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            raise
    elif choice == "0":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice. Please enter 0-4.")
        sys.exit(1)


if __name__ == "__main__":
    main()
