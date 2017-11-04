import json
import time

import requests

from utils import ENDPOINT, headers, deprecated, fetch_category_list
from utils.parsers import parse_attributes, parse_spells

npcs = []


def fetch_npc_list():
    start_time = time.time()
    print("Fetching npc list...")
    fetch_category_list("Category:NPCs", npcs)
    print(f"\t{len(npcs):,} npcs found in {time.time()-start_time:.3f} seconds.")

    for d in deprecated:
        if d in npcs:
            npcs.remove(d)
    print(f"\t{len(npcs):,} npcs after removing deprecated npcs.")


def fetch_npcs(con):
    print("Fetching npc information...")
    start_time = time.time()
    i = 0
    spell_counter = 0
    while True:
        if i > len(npcs):
            break
        params = {
            "action": "query",
            "prop": "revisions",
            "rvprop": "content",
            "format": "json",
            "titles": "|".join(npcs[i:min(i + 50, len(npcs))])
        }

        r = requests.get(ENDPOINT, headers=headers, params=params)
        data = json.loads(r.text)
        npc_pages = data["query"]["pages"]
        i += 50
        attribute_map = {
            "title": "name",
            "name": "actualname",
            "job": "job",
            "city": "city",
            "version": "implemented"
        }
        c = con.cursor()
        for article_id, article in npc_pages.items():
            skip = False
            content = article["revisions"][0]["*"]
            if "{{Infobox NPC" not in content:
                # Skipping pages like creature groups articles
                continue
            npc = parse_attributes(content)
            tup = ()
            for sql_attr, wiki_attr in attribute_map.items():
                try:
                    # Attribute special cases
                    # If no actualname is found, we assume it is the same as title
                    if wiki_attr == "actualname" and npc.get(wiki_attr) in [None, ""]:
                        value = npc["name"]
                    else:
                        value = npc[wiki_attr]
                    tup = tup + (value,)
                except KeyError:
                    tup = tup + (None,)
                except:
                    print(f"Unknown exception found for {article['title']}")
                    print(npc)
                    skip = True
            if skip:
                continue
            c.execute(f"INSERT INTO npcs({','.join(attribute_map.keys())}) "
                      f"VALUES({','.join(['?']*len(attribute_map.keys()))})", tup)
            npc_id = c.lastrowid
            if "sells" in npc and 'teaches' in npc["sells"].lower():
                spell_list = parse_spells(npc["sells"])
                spell_data = []
                for group, spells in spell_list:
                    for spell in spells:
                        c.execute("SELECT id FROM spells WHERE name LIKE ?", (spell.strip(),))
                        result = c.fetchone()
                        if result is None:
                            continue
                        spell_id = result[0]
                        knight = paladin = sorcerer = druid = False
                        if "knight" in group.lower():
                            knight = True
                        elif "paladin" in group.lower():
                            paladin = True
                        elif "druid" in group.lower():
                            druid = True
                        elif "sorcerer" in group.lower():
                            sorcerer = True
                        else:
                            def in_jobs(vocation, _npc):
                                return vocation in _npc.get("job", "").lower() \
                                       or vocation in _npc.get("job2", "").lower() \
                                       or vocation in _npc.get("job3", "").lower()
                            knight = in_jobs("knight", npc)
                            paladin = in_jobs("paladin", npc)
                            druid = in_jobs("druid", npc)
                            sorcerer = in_jobs("sorcerer", npc)
                        exists = False
                        # Exceptions:
                        if npc["name"] == "Ursula":
                            paladin = True
                        elif npc["name"] == "Eliza":
                            paladin = druid = sorcerer = knight = True
                        elif npc["name"] == "Elathriel":
                            druid = True
                        for j, s in enumerate(spell_data):
                            # Spell was already in list, so we update vocations
                            if s[1] == spell_id:
                                spell_data[j] = [npc_id, s[1], s[2] or knight, s[3] or paladin, s[4] or druid, s[5] or sorcerer]
                                exists = True
                                break
                        if not exists:
                            spell_data.append([npc_id, spell_id, knight, paladin, druid, sorcerer])
                c.executemany("INSERT INTO npcs_spells(npc_id, spell_id, knight, paladin, druid, sorcerer) "
                              "VALUES(?,?,?,?,?,?)", spell_data)
                spell_counter += c.rowcount
        con.commit()
        c.close()
    print(f"\t{spell_counter:,} teachable spells added.")
    print(f"\tDone in {time.time()-start_time:.3f} seconds.")
