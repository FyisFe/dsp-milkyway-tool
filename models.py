#!/usr/bin/env python3

from dataclasses import dataclass


@dataclass
class PlayerData:
    """Represents a single player's data in the top ten leaderboard."""

    seed: int
    stars: int
    resource_multiplier: str
    combat_difficulty: str
    user_id: int
    platform: str
    account_name: str
    generation_capacity: str
    is_anonymous: bool


@dataclass
class SeedData:
    """Represents aggregated data for a specific seed."""

    seed: int
    stars: int
    resource_multiplier: str
    combat_difficulty: str
    player_count: int
    total_generation_capacity: str


@dataclass
class Summary:
    """Represents global summary statistics."""

    total_players: int
    total_generation_capacity: str
    total_sails_launched: int
    total_dyson_spheres: int
