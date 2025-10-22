import requests
import random

SERVER_ADDRESS = "http://8.140.162.132/"
LOGIN_HEADER_API = "login/header"
DOWNLOAD_FULL_DATA_API = "download"

def generate_random_steam_user_id() -> int:
    """Generate a random Steam user ID."""

    return 1 | (1 << 32) | (1 << 52) | (1 << 56) | ((random.getrandbits(31)) << 1)


def http_get(url: str) -> bytes:
    """Perform an HTTP GET request and return the response content."""

    response = requests.get(url)
    response.raise_for_status()
    return response.content


def login(user_id: int) -> str:
    """
    Log in to the server with the given user ID and return the response data.

     Args:
          user_id (int): The Steam user ID to log in with.
     Returns:
             str: The response data from the server. "<login_key>,<full_data_url>"
    """

    response = http_get(f"{SERVER_ADDRESS}{LOGIN_HEADER_API}?user_id={user_id}")
    return response.decode("utf-8")

def fetch_full_data(full_data_url: str) -> bytes:
    """
    Fetch the full data from the given URL.

    Args:
        full_data_url (str): The URL to fetch the full data from.

    Returns:
        bytes: The full data content.
    """

    return http_get(f"{SERVER_ADDRESS}{DOWNLOAD_FULL_DATA_API}/{full_data_url}")