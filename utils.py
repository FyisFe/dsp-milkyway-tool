#!/usr/bin/env python3

import random
import requests

SERVER_ADDRESS = "http://8.140.162.132/"
LOGIN_HEADER_API = "login/header"
DOWNLOAD_FULL_DATA_API = "download"


def generate_random_steam_user_id() -> int:
    """
    Generate a random Steam user ID.

    Returns:
        A valid Steam user ID with proper bit flags set
    """
    return 1 | (1 << 32) | (1 << 52) | (1 << 56) | ((random.getrandbits(31)) << 1)


def http_get(url: str) -> bytes:
    """
    Perform an HTTP GET request and return the response content.

    Args:
        url: The URL to fetch

    Returns:
        Response content as bytes

    Raises:
        requests.HTTPError: If the request fails
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def login(user_id: int) -> str:
    """
    Log in to the server with the given user ID and return the response data.

    Args:
        user_id: The Steam user ID to log in with

    Returns:
        The response data from the server in format "<login_key>,<full_data_url>"

    Raises:
        requests.HTTPError: If the request fails
    """
    response = http_get(f"{SERVER_ADDRESS}{LOGIN_HEADER_API}?user_id={user_id}")
    return response.decode("utf-8")


def fetch_full_data(full_data_url: str) -> bytes:
    """
    Fetch the full data from the given URL.

    Args:
        full_data_url: The URL path to fetch the full data from

    Returns:
        The full data content as bytes

    Raises:
        requests.HTTPError: If the request fails
    """
    return http_get(f"{SERVER_ADDRESS}{DOWNLOAD_FULL_DATA_API}/{full_data_url}")