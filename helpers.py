#!/usr/bin/env python3


def platform_name(pid: int) -> str:
    """Convert platform ID to platform name."""
    return {1: "Steam", 2: "WeGame", 3: "XGP"}.get(pid, "Standalone")


def resource_multiplier(n: int) -> str:
    """Convert resource multiplier value to string representation."""
    if n == 99:
        return "无限"
    return f"{n / 10.0:.1f}"


def combat_mode_difficulty_number(n: int) -> str:
    """Convert combat mode difficulty value to string representation."""
    if (n // 100) == 0:
        return "和平模式"
    return str(n % 100)


def format_generation_capacity(watts: int) -> str:
    """
    Format generation capacity with appropriate unit (W, MW, GW, TW, PW).

    Args:
        watts: Generation capacity in watts (W)

    Returns:
        Formatted string with appropriate unit (e.g., "1.5 GW", "250 MW")
    """
    units = [
        (1_000_000_000_000_000, "PW"),  # Petawatts
        (1_000_000_000_000, "TW"),      # Terawatts
        (1_000_000_000, "GW"),          # Gigawatts
        (1_000_000, "MW"),              # Megawatts
        (1_000, "kW"),                  # Kilowatts
        (1, "W"),                       # Watts
    ]

    for threshold, unit in units:
        if watts >= threshold:
            value = watts / threshold
            # Format with appropriate precision
            if value >= 100:
                return f"{value:.0f} {unit}"
            elif value >= 10:
                return f"{value:.1f} {unit}"
            else:
                return f"{value:.2f} {unit}"

    return f"{watts} W"


def decode_seed_key(seed_key: int) -> tuple[int, int, str, str]:
    """
    Decode a seed key into its components.

    Args:
        seed_key: The seed key to decode

    Returns:
        Tuple of (seed, stars, resource_multiplier, combat_difficulty)
    """
    seed = seed_key // 100_000_000
    stars = (seed_key // 100_000) % 1000
    res_mult = resource_multiplier((seed_key // 1000) % 100)
    combat = combat_mode_difficulty_number(seed_key % 1000)
    return seed, stars, res_mult, combat
