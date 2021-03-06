import re

from typing import Optional, Dict, List

creature_loot_pattern = re.compile(r"\|{{Loot Item\|(?:([\d?+-]+)\|)?([^}|]+)")
min_max_pattern = re.compile(r"(\d+)-(\d+)")
loot_stats_pattern = re.compile(r"\|([\s\w]+),\s*times:(\d+)(?:,\s*amount:([\d-]+))?")
kills_pattern = re.compile(r"kills=(\d+)")
int_pattern = re.compile(r"[+-]?\d+")
float_pattern = re.compile(r'[+-]?(\d*[.])?\d+')
named_links_pattern = re.compile(r'\[\[[^]|]+\|([^]]+)\]\]')
link_pattern = re.compile(r'\[\[([^|\]]+)')
links_pattern = re.compile(r'\[\[([^]]+)\]\]')
external_links_pattern = re.compile(r'\[[^]]+\]')

teaches_template = re.compile(r"{{Teaches\s*(?:\|name=([^|]+))?([^}]+)}}")
spells_pattern = re.compile(r"\|([^|]+)")

price_to_template = re.compile(r"{{Price to (?:Buy|Sell)\s*([^}]+)}}")
npc_offers = re.compile(r"\|([^|:\[]+)(?::\s?(\d+))?(?:\s?\[\[([^\]]+))?")

trades_sell_template = re.compile(r"{{Trades/Sells\s*(?:\|note=([^|]+))?([^}]+)}}")
npc_trades = re.compile(r"\|([^|,\[]+)(?:,\s?([+-]?\d+))?(?:\s?\[\[([^\]]+))?")

transport_template = re.compile(r"{{Transport\s*(?:\|discount=([^|]+))?([^}]+)}}")
npc_destinations = re.compile(r"\|([^,]+),\s?(\d+)(?:;\s?([^|]+))?")


def parse_item_offers(value: str) -> List:
    match = price_to_template.search(value)
    if match:
        return npc_offers.findall(match.group(1))
    else:
        return []


def parse_item_trades(value: str) -> List:
    result = []
    for note, trades in trades_sell_template.findall(value):
        result.extend(npc_trades.findall(trades))
    return result


def parse_destinations(value: str) -> List:
    result = []
    for __, destinations in transport_template.findall(value):
        result.extend(npc_destinations.findall(destinations))
    return result


def parse_loot(value: str):
    return creature_loot_pattern.findall(value)


def parse_loot_statistics(value):
    match = kills_pattern.search(value)
    if match:
        return int(match.group(1)), loot_stats_pattern.findall(value)
    else:
        return 0, None


def parse_min_max(value):
    match = min_max_pattern.search(value)
    if match:
        return int(match.group(1)), int(match.group(2))
    else:
        return 0, parse_integer(value, 1)


def parse_integer(value: str, default=0):
    if value is None:
        return default
    match = int_pattern.search(value)
    if match:
        return int(match.group(0))
    else:
        return default


def parse_float(value: str, default=0):
    if value is None:
        return default
    match = float_pattern.search(value)
    if match:
        return float(match.group(0))
    else:
        return default


def parse_maximum_integer(value: str) -> Optional[int]:
    if value is None:
        return None
    matches = int_pattern.findall(value)
    try:
        return max(list(map(int, matches)))
    except ValueError:
        return None


def parse_boolean(value: str):
    return value is None or value.strip().lower() == "yes"


def clean_links(content):
    if content is None:
        return None
    # Named links
    content = named_links_pattern.sub('\g<1>', content)
    # Links
    content = links_pattern.sub('\g<1>', content)
    # External links
    content = external_links_pattern.sub('', content)
    # Double spaces
    content = content.replace('  ', ' ')
    return content


def parse_attributes(content) -> Dict[str, str]:
    attributes = dict()
    depth = 0
    parse_value = False
    attribute = ""
    value = ""
    for i in range(len(content)):
        if content[i] == '{' or content[i] == '[':
            depth += 1
            if depth >= 3:
                if parse_value:
                    value = value + content[i]
                else:
                    attribute = attribute + content[i]
        elif content[i] == '}' or content[i] == ']':
            if depth >= 3:
                if parse_value:
                    value = value + content[i]
                else:
                    attribute = attribute + content[i]
            if depth == 2:
                attributes[attribute.strip()] = value.strip()
                parse_value = False
                attribute = ""
                value = ""
            depth -= 1
        elif content[i] == '=' and depth == 2:
            parse_value = True
        elif content[i] == '|' and depth == 2:
            attributes[attribute.strip()] = value.strip()
            parse_value = False
            attribute = ""
            value = ""
        elif parse_value:
            value = value + content[i]
        else:
            attribute = attribute + content[i]
    return dict((k, v.strip()) for k, v in attributes.items() if v.strip())


def parse_spells(value):
    result = []
    for name, spell_list in teaches_template.findall(value):
        spells = spells_pattern.findall(spell_list)
        spells = [s.strip() for s in spells]
        result.append((name, spells))
    return result


def convert_tibiawiki_position(pos) -> int:
    """Converts from TibiaWiki position system to regular numeric coordinates

    TibiaWiki takes the coordinates and splits in two bytes, represented in decimal, separated by a period."""
    position_splits = pos.strip().split(".")
    try:
        coordinate = int(position_splits[0]) << 8
        if len(position_splits) > 1 and position_splits[1].strip():
            coordinate += int(position_splits[1])
        return coordinate
    except (ValueError, IndexError):
        return 0


def parse_links(value):
    return list(link_pattern.findall(value))
