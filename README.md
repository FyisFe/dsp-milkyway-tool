# DSP Milky Way Tool

A Python tool for downloading and parsing Dyson Sphere Program Milky Way server data.

> Don’t blame me for the code smells and duplicates — it’s pure vibe coding, and hey, it works.
> i18n still pending, so enjoy the Mandarin-English fusion for now

## Features

- Download Milky Way statistics (total players, generation capacity, Dyson spheres, etc.)
- Download full game data
- Download all user data to CSV
- Search and download cluster players by seed parameters

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the interactive menu:

```bash
python main.py
```

Choose from the following options:
1. Download statistics data
2. Download full data
3. Download all user data
4. Download cluster players by seed

Output files are saved to the `output/` directory.

## Sample Result 

### Result from Option 1 (Statistics Data)

```
总玩家数: 1383854
总发电量: 1131 PW
总太阳帆数: 33027194053060
总戴森球数: 1951718
```

### Result from Option 2

- all.csv 
```
种子,星数,资源倍率,战斗难度,用户数,总发电量
99957695,49,5.0,0,5,19.7 PW
95889621,60,0.5,和平模式,1,19.6 PW
```

- summary.txt

```
总玩家数: 1383839
总发电量: 1131 PW
总太阳帆数: 33026904013530
总戴森球数: 1951694
```

- top_ten.csv
```
种子,星数,资源倍率,战斗难度,用户ID,平台,账号,发电量,匿名
99957695,49,5.0,0,76561198289063708,Steam,淡蓝记忆,19.7 PW,False
95889621,60,0.5,和平模式,76561199148673589,Steam,都是渣渣,19.6 PW,False
50980865,64,0.1,99,76561199233012278,Steam,096096,19.5 PW,False
95889621,61,0.1,10,76561198935814098,Steam,星见镇的丝缇涅尔,19.5 PW,False
20070903,52,0.1,和平模式,76561199233012278,Steam,096096,19.5 PW,False
50980865,64,无限,和平模式,76561199415486815,Steam,Sakura1618,19.2 PW,False
50980865,43,1.0,57,76561198107727293,Steam,Arcueid Brunestud,19.1 PW,False
91346466,64,无限,和平模式,76561198199131943,Steam,名字748,19.0 PW,False
50980865,64,无限,10,76561199695911021,Steam,超级大磁場,18.8 PW,False
99048983,64,1.0,和平模式,76561199088990142,Steam,祈雨,18.6 PW,False
```

### Result from Option 3 

- users.csv
```
种子,星数,资源倍率,战斗难度,用户ID,平台,账号,发电量,匿名
<xxx>,64,无限,和平模式,<xxx>,Steam,<xxx>,2.83 GW,False
<xxx>,64,无限,和平模式,<xxx>,Steam,<xxx>,8.12 GW,False
```

### Result from Option 4

- cluster_players.csv
```
种子,星数,资源倍率,战斗难度,用户ID,平台,账号,发电量,匿名
1,64,无限,和平模式,76561198835860351,Steam,Echone,113 TW,False
1,64,无限,和平模式,76561198147877429,Steam,noom,39.8 TW,False
1,64,无限,和平模式,76561199226329187,Steam,Wraith.,17.0 TW,False
```

## Requirements

- Python 3.x
- requests
