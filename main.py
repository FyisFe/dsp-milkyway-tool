#!/usr/bin/env python3

import logging

from downloader import FullDataDownloader


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> None:
    """Main entry point for the DSP Milky Way data downloader."""
    setup_logging()
    logger = logging.getLogger(__name__)

    try:
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

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise


if __name__ == "__main__":
    main()
