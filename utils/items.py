import re
import time
from typing import Tuple, Dict, Callable

from utils import deprecated, fetch_category_list, fetch_article_images, fetch_articles, log
from utils.database import get_row_count
from utils.parsers import parse_attributes, parse_boolean, parse_float, parse_integer

items = []


def fetch_items_list():
    print("Fetching item list... ")
    start_time = time.time()
    fetch_category_list("Category:Items", items)
    print(f"\t{len(items):,} found")
    for d in deprecated:
        if d in items:
            items.remove(d)
    print(f"\t{len(items):,} after removing deprecated articles.")
    print(f"\tDone in {time.time()-start_time:.3f} seconds.")


def fetch_items(con):
    print("Fetching items information...")
    start_time = time.time()
    exception_count = 0
    attribute_map = {
        "name": ("title", lambda x: x),
        "actualname": ("name", lambda x: x),
        "weight": ("weight", lambda x: parse_float(x)),
        "stackable": ("stackable", lambda x: parse_boolean(x)),
        "npcvalue": ("value", lambda x: parse_integer(x)),
        "npcprice": ("price", lambda x: parse_integer(x)),
        "flavortext": ("flavor_text", lambda x: x),
        "primarytype": ("type", lambda x: x),
        "implemented": ("version", lambda x: x),
    }  # type: Dict[str, Tuple[str, Callable]]
    c = con.cursor()
    for article_id, article in fetch_articles(items):
        try:
            content = article["revisions"][0]["*"]
            if "{{Infobox Item|" not in content:
                # Skipping page without Infoboxes
                continue
            item = parse_attributes(content)
            columns = []
            values = []
            if "actualname" not in item:
                item["actualname"] = item["name"].lower()
            for attribute, value in item.items():
                if attribute not in attribute_map:
                    continue
                column, func = attribute_map[attribute]
                columns.append(column)
                values.append(func(value))
            c.execute(f"INSERT INTO items({','.join(columns)}) VALUES({','.join(['?']*len(values))})", values)
            item_id = c.lastrowid
            extra_attributes = {
                "level": "levelrequired",
                "attack": "attack",
                "element_attack": "elementattack",
                "defense": "defense",
                "defensemod": "defensemod",
                "armor": "armor",
                "hands": "hands",
                "imbueslots": "imbueslots",
                "attack+": "atk_mod",
                "hit%+": "hit_mod",
                "range": "range",
                "damagetype": "damagetype",
                "damage": "damage",
                "mana": "mana",
                "magic_level": "mlrequired",
                "words": "words",
                "critical_chance": "crithit_ch",
                "critical%": "critextra_dmg",
                "hpleech_chance": "hpleech_ch",
                "hpleech%": "hpleech_am",
                "manaleech_chance": "manaleech_ch",
                "manaleech%": "manaleech_am",
                "volume": "volume",
                "charges": "charges",
                "food_time": "regenseconds",
                "duration": "duration",
            }
            extra_data = []
            for sql_attr, wiki_attr in extra_attributes.items():
                if wiki_attr in item and item[wiki_attr]:
                    extra_data.append((item_id, sql_attr, item[wiki_attr]))
            # These attributes require some extra processing
            if "resist" in item and item["resist"]:
                resistances = item["resist"].split(",")
                for element in resistances:
                    element = element.strip()
                    m = re.search(r'([a-zA-Z0-9_ ]+) +(-?\+?\d+)%', element)
                    if m:
                        attribute = m.group(1) + "%"
                        try:
                            value = int(m.group(2))
                        except ValueError:
                            value = 0
                        extra_data.append((item_id, attribute, value))
            if "attrib" in item and item["attrib"]:
                attribs = item["attrib"].split(",")
                for attr in attribs:
                    attr = attr.strip()
                    m = re.search(r'([\s\w]+)\s([+\-\d]+)', attr)
                    if m:
                        attribute = m.group(1).replace("fighting", "").replace("level", "").strip()
                        value = m.group(2)
                        extra_data.append((item_id, attribute, value))
            if "imbuements" in item and item["imbuements"]:
                imbuements = item["imbuements"].split(",")
                for imbuement in imbuements:
                    imbuement = imbuement.strip()
                    extra_data.append((item_id, "imbuement", imbuement))
            if "vocrequired" in item and item["vocrequired"] and item["vocrequired"] != "None":
                vocation = item['vocrequired'].replace('knights', 'k').replace('druids', 'd') \
                    .replace('sorcerers', 's').replace('paladins', 'p').replace(' and ', '+')
                extra_data.append((item_id, "vocation", vocation))
            c.executemany("INSERT INTO items_attributes(item_id, attribute, value) VALUES(?,?,?)", extra_data)
        except Exception:
            log.exception(f"Unknown exception found for {article['title']}")
            exception_count += 1
            continue
    con.commit()
    c.close()
    rows = get_row_count(con, "items")
    attributes_row = get_row_count(con, "items_attributes")
    print(f"\t{rows:,} entries added to table")
    print(f"\t{attributes_row:,} attributes added to table")
    if exception_count:
        print(f"\t{exception_count:,} exceptions found, check errors.log for more information.")
    print(f"\tDone in {time.time()-start_time:.3f} seconds.")


def fetch_item_images(con):
    print("Fetching item images...")
    start_time = time.time()
    fetch_count, cache_count, missing_count, failed_count = fetch_article_images(con, items, "items")
    print(f"\tFetched {fetch_count:,} images, loaded {cache_count:,} from cache.")
    print(f"\t{missing_count:,} items with no image.")
    if failed_count > 0:
        print(f"\t{failed_count:,} images failed fetching.")
    print(f"\tDone in {time.time()-start_time:.3f} seconds.")
