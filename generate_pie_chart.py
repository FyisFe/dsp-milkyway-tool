#!/usr/bin/env python3
"""
Generate a pie chart aggregating generation capacity by Steam ID.
Downloads cluster data for seeds with > 100TW generation capacity.
"""

import csv
import logging
import os
import re
import time
from collections import defaultdict

import matplotlib.pyplot as plt
from cluster_player_downloader import ClusterPlayerDownloader
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_power_to_watts(power_str: str) -> int:
    """
    Parse power strings like "20.6 PW", "100 TW", "1000 kW", "1000 KW" to watts.
    """
    s = power_str.strip()
    # allow commas like "1,000 kW"
    s = s.replace(",", "")

    match = re.match(r'^([\d.]+)\s*([a-zA-Z]+W?)$', s)
    if not match:
        logger.warning(f"Could not parse power string: {power_str}")
        return 0

    value = float(match.group(1))
    unit = match.group(2).strip().lower()  # normalize: "kW", "KW" -> "kw"

    multipliers = {
        'pw': 1_000_000_000_000_000,
        'tw': 1_000_000_000_000,
        'gw': 1_000_000_000,
        'mw': 1_000_000,
        'kw': 1_000,
        'w': 1,
    }

    # handle cases like "kw" vs "kw" (already) and optional missing W
    unit = unit if unit.endswith('w') else unit + 'w'

    return int(value * multipliers.get(unit, 1))
def resource_multiplier_to_raw(mult_str: str) -> int:
    """Convert resource multiplier string to raw value."""
    if mult_str == "无限":
        return 99
    return int(float(mult_str) * 10)


def combat_difficulty_to_raw(diff_str: str) -> int:
    """Convert combat difficulty string to raw value."""
    if diff_str == "和平模式":
        return 0
    if (len(diff_str) == 1):
        return int("10" + diff_str)
    
    return int("1" + diff_str)


def load_high_capacity_seeds(all_csv_path: str, min_watts: int = 100_000_000_000_000) -> list[dict]:
    """
    Load seeds from all.csv with generation capacity > min_watts.

    Args:
        all_csv_path: Path to all.csv file
        min_watts: Minimum generation capacity in watts (default: 100 TW)

    Returns:
        List of seed dictionaries with seed info
    """
    high_capacity_seeds = []

    logger.info(f"Reading {all_csv_path}...")

    with open(all_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            gen_cap_watts = parse_power_to_watts(row['总发电量'])

            if gen_cap_watts >= min_watts:
                seed_info = {
                    'seed': int(row['种子']),
                    'stars': int(row['星数']),
                    'resource_mult': row['资源倍率'],
                    'combat_diff': row['战斗难度'],
                    'gen_cap_watts': gen_cap_watts,
                    'gen_cap_str': row['总发电量'],
                    'user_count': int(row['用户数'])
                }
                high_capacity_seeds.append(seed_info)

    logger.info(f"Found {len(high_capacity_seeds)} seeds with > {min_watts / 1_000_000_000_000:.0f} TW")

    return high_capacity_seeds


def download_cluster_data_for_seeds(seeds: list[dict], config: Config) -> list[dict]:
    """
    Download cluster player data for all seeds.

    Args:
        seeds: List of seed info dictionaries
        config: Configuration object

    Returns:
        List of player dictionaries with steam_id, name, gen_cap_watts
    """
    downloader = ClusterPlayerDownloader(config=config)
    all_players = []

    for i, seed_info in enumerate(seeds):
        time.sleep(0.5)  # Be polite to the server
        logger.info(f"\n=== Processing seed {i+1}/{len(seeds)} ===")
        logger.info(f"Seed: {seed_info['seed']}, Stars: {seed_info['stars']}, "
                   f"Resource: {seed_info['resource_mult']}, Combat: {seed_info['combat_diff']}")
        logger.info(f"Total generation: {seed_info['gen_cap_str']} ({seed_info['user_count']} users)")

        # Convert to raw values for API
        resource_mult_raw = resource_multiplier_to_raw(seed_info['resource_mult'])
        combat_diff_raw = combat_difficulty_to_raw(seed_info['combat_diff'])

        try:
            # Download cluster data
            players = downloader.download_and_parse_cluster_players(
                seed=seed_info['seed'],
                stars=seed_info['stars'],
                resource_mult=resource_mult_raw,
                combat_diff=combat_diff_raw,
                max_pages=2
            )
            
            # append into a csv file for reference
            csv_path = os.path.join(config.output_dir, f"player.csv")
            with open(csv_path, 'a', encoding='utf-8', newline='') as csvfile:
                fieldnames = ['种子', '星数', '资源倍率', '战斗难度', '用户ID', '平台', '账号', '发电量', '匿名']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if os.path.getsize(csv_path) == 0:
                    writer.writeheader()
                for player in players:
                    writer.writerow({
                        '种子': seed_info['seed'],
                        '星数': seed_info['stars'],
                        '资源倍率': seed_info['resource_mult'],
                        '战斗难度': seed_info['combat_diff'],
                        '用户ID': player.user_id,
                        '平台': player.platform,
                        '账号': player.account_name,
                        '发电量': player.generation_capacity,
                        '匿名': player.is_anonymous
                    }) 
        

            # Convert to simplified format
            for player in players:
                # Only include Steam players (platform ID 1)
                if player.platform == "Steam":
                    gen_cap_watts = parse_power_to_watts(player.generation_capacity)
                    all_players.append({
                        'steam_id': player.user_id,
                        'name': player.account_name,
                        'gen_cap_watts': gen_cap_watts
                    })

            logger.info(f"Added {len([p for p in players])} Steam players from this seed")

        except Exception as e:
            logger.error(f"Failed to download cluster data for seed {seed_info['seed']}: {e}")
            continue

    logger.info(f"\n=== Total: {len(all_players)} Steam player records ===")
    return all_players

def aggregate_by_steam_id(players: list[dict]) -> dict:
    """
    Aggregate players by Steam ID, collecting all usernames and summing generation capacity.

    Args:
        players: List of player dictionaries

    Returns:
        Dictionary mapping steam_id to {'names': set, 'total_gen_cap': int}
    """
    aggregated = defaultdict(lambda: {'names': set(), 'total_gen_cap': 0})

    for player in players:
        steam_id = player['steam_id']
        aggregated[steam_id]['names'].add(player['name'])
        aggregated[steam_id]['total_gen_cap'] += player['gen_cap_watts']

    logger.info(f"Aggregated {len(players)} records into {len(aggregated)} unique Steam IDs")

    return dict(aggregated)


def generate_pie_chart(aggregated: dict, output_path: str, top_n: int = 30):
    """
    Generate a pie chart of generation capacity by Steam ID.

    Args:
        aggregated: Dictionary of {steam_id: {'names': set, 'total_gen_cap': int}}
        output_path: Path to save the chart
        top_n: Number of top users to show individually (others grouped as "Others")
    """
    # Configure font to support Chinese characters
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "Noto Sans CJK", "WenQuanYi Zen Hei", "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False


    # Sort by generation capacity
    sorted_users = sorted(aggregated.items(), key=lambda x: x[1]['total_gen_cap'], reverse=True)

    # Prepare data for pie chart
    labels = []
    sizes = []

    # Top N users
    for steam_id, data in sorted_users[:top_n]:
        # Combine all names with " / "
        display_name = ' / '.join(sorted(data['names']))
        # Truncate if too long
        if len(display_name) > 50:
            display_name = display_name[:47] + '...'

        label = f"{display_name}"
        labels.append(label)
        sizes.append(data['total_gen_cap'])

    # Group remaining as "Others"
    if len(sorted_users) > top_n:
        others_total = sum(data['total_gen_cap'] for _, data in sorted_users[top_n:])
        others_tw = others_total / 1_000_000_000_000_000
        labels.append(f"杂鱼们 (共{len(sorted_users) - top_n} 杂鱼)\n({others_tw:.1f} PW)")
        sizes.append(others_total)

    # Create pie chart
    plt.figure(figsize=(14, 10))
    colors = plt.cm.Set3.colors

    # Custom autopct function to show generation capacity instead of percentage
    def make_autopct(values):
        def autopct_func(pct):
            total = sum(values)
            val = pct * total / 100.0
            gen_cap_pw = val / 1_000_000_000_000_000
            return f'{gen_cap_pw:.1f} PW'
        return autopct_func

    plt.pie(sizes, labels=labels, autopct=make_autopct(sizes), startangle=90, colors=colors)
    plt.title('银河系发电统计 (只统计大于200 TW星区，每星区仅统计前20名用户)', fontsize=16, fontweight='bold')
    plt.axis('equal')

    # Save chart
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    logger.info(f"Pie chart saved to: {output_path}")

    # Also show statistics
    logger.info("\n=== Top 10 Users by Generation Capacity ===")
    
    # save all sorted users to a csv for reference
    stats_csv_path = os.path.splitext(output_path)[0] + '_stats.csv'
    with open(stats_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['Rank', 'Steam ID', 'Names', 'Generation Capacity (PW)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i, (steam_id, data) in enumerate(sorted_users, 1):
            names = ' / '.join(sorted(data['names']))
            gen_cap_tw = data['total_gen_cap'] / 1_000_000_000_000_000
            writer.writerow({
                'Rank': i,
                'Steam ID': steam_id,
                'Names': names,
                'Generation Capacity (PW)': f"{gen_cap_tw:.2f}"
            })
    logger.info(f"Statistics saved to: {stats_csv_path}")
    
    for i, (steam_id, data) in enumerate(sorted_users[:10], 1):
        names = ' / '.join(sorted(data['names']))
        gen_cap_tw = data['total_gen_cap'] / 1_000_000_000_000_000
        logger.info(f"{i}. Steam ID {steam_id}: {names} - {gen_cap_tw:.2f} PW")


def main():
    """Main function to generate pie chart."""
    config = Config()

    # Path to all.csv
    all_csv_path = os.path.join(config.output_dir, 'all.csv')

    if not os.path.exists(all_csv_path):
        logger.error(f"all.csv not found at {all_csv_path}")
        logger.error("Please download full data first using the main downloader.")
        return

    # Step 1: Load seeds with > 200 TW
    logger.info("Step 1: Loading high-capacity seeds from all.csv...")
    high_capacity_seeds = load_high_capacity_seeds(str(all_csv_path), min_watts=200_000_000_000_000)

    if not high_capacity_seeds:
        logger.warning("No seeds found with > 200 TW generation capacity")
        return

    # Step 2: Download cluster data for these seeds
    logger.info("\nStep 2: Downloading cluster data for high-capacity seeds...")
    all_players = download_cluster_data_for_seeds(high_capacity_seeds, config)

    if not all_players:
        logger.warning("No player data downloaded")
        return

    # Step 3: Aggregate by Steam ID
    logger.info("\nStep 3: Aggregating data by Steam ID...")
    aggregated = aggregate_by_steam_id(all_players)

    # Step 4: Generate pie chart
    logger.info("\nStep 4: Generating pie chart...")
    output_path = os.path.join(config.output_dir, 'generation_capacity_pie_chart.png')
    generate_pie_chart(aggregated, output_path, top_n=20)

    logger.info("\n=== Done! ===")


if __name__ == '__main__':
    main()
