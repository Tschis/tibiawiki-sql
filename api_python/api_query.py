import time
import sqlite3

DATABASE_FILE = '../tibia_database.db'
DEFAULT_SELECT = 'SELECT * FROM {} '
DEFAULT_WHERE = ' WHERE {} '
DEFAULT_WHERE_LIKE = DEFAULT_WHERE + ' LIKE ? '
DEFAULT_WHERE_EQUAL = DEFAULT_WHERE + ' = ? '
DEFAULT_WHERE_NOT_EQUAL = DEFAULT_WHERE + ' <> ? '
DEFAULT_ORDER_BY = ' ORDER BY {} ASC '
TABLE_CREATURES = 'creatures'
TABLE_ITEMS = 'items'
TABLE_NPCS = 'npcs'
TABLE_QUESTS = 'quests'
TABLE_SPELLS = 'spells'
NAME_COLUMN = 'name'


def get_summonable_creatures():
    filtered_column = 'summon'
    filtered_param = 0
    return __get_entity__(TABLE_CREATURES, filtered_column, filtered_param, DEFAULT_WHERE_NOT_EQUAL)


def get_convincible_creatures():
    filtered_column = 'convince'
    filtered_param = 0
    return __get_entity__(TABLE_CREATURES, filtered_column, filtered_param, DEFAULT_WHERE_NOT_EQUAL)


def get_creature_by_exact_name(creature_name):
    return __get_creature__(NAME_COLUMN, creature_name)


def get_creature_by_name(creature_name):
    return __get_creature__(NAME_COLUMN, add_wildcards(creature_name))


def __get_creature__(filtered_column, filtered_param):
    return __get_entity__(TABLE_CREATURES, filtered_column, filtered_param)


def get_item_by_exact_name(item_name):
    return __get_item__(NAME_COLUMN, item_name)


def get_item_by_name(item_name):
    return __get_item__(NAME_COLUMN, add_wildcards(item_name))


def __get_item__(filtered_column, filtered_param):
    return __get_entity__(TABLE_ITEMS, filtered_column, filtered_param)


def get_npc_by_exact_name(npc_name):
    return __get_npc__(NAME_COLUMN, npc_name)


def get_npc_by_name(npc_name):
    return __get_npc__(NAME_COLUMN, add_wildcards(npc_name))


def __get_npc__(filtered_column, filtered_param):
    return __get_entity__(TABLE_NPCS, filtered_column, filtered_param)


def get_spell_by_exact_name(spell_name):
    return __get_spell__(NAME_COLUMN, spell_name)


def get_spell_by_name(spell_name):
    return __get_spell__(NAME_COLUMN, add_wildcards(spell_name))


def __get_spell__(filtered_column, filtered_param):
    return __get_entity__(TABLE_SPELLS, filtered_column, filtered_param)


def get_quest_by_exact_name(quest_name):
    return __get_quest__(NAME_COLUMN, quest_name)


def get_quest_by_name(quest_name):
    return __get_quest__(NAME_COLUMN, add_wildcards(quest_name))


def __get_quest__(filtered_column, filtered_param):
    return __get_entity__(TABLE_QUESTS, filtered_column, filtered_param,)


def __get_entity__(table_name, filtered_column, filtered_param, where=None, order_by=None):
    entities = []
    con = get_connection()
    cursor = con.cursor()
    try:
        start_time = time.time()
        results = execute_query(cursor, table_name, filtered_column, where, order_by, filtered_param)
        num_fields = len(cursor.description)
        field_names = [i[0] for i in cursor.description]

        for result in results:
            entity = {}
            for i in range(0, num_fields):
                entity[field_names[i]] = result[i]

            entities.append(entity)

        if len(entities) == 0:
            print("No rows found.")
        else:
            print("{} rows found.".format(len(entities)))

        print(f"Done in {time.time()-start_time:.3f} seconds.")
    except Exception as e:
        print(e)
    finally:
        cursor.close()
        con.close()

    return entities


def execute_query(cursor, table_name, filtered_column, where, order_by, filtered_param):
    sql = DEFAULT_SELECT.format(table_name)
    sql = add_where_clause(sql, filtered_column, where)
    sql = add_order_by_clause(sql, filtered_column, order_by)
    print(sql)
    cursor.execute(sql, (filtered_param,))
    return cursor.fetchall()


def add_order_by_clause(sql, filtered_column, order_by):
    if not order_by:
        sql += DEFAULT_ORDER_BY.format(filtered_column)
    else:
        sql += order_by
    return sql


def add_where_clause(sql, filtered_column, where):
    if not where:
        sql += DEFAULT_WHERE_LIKE
    else:
        sql += where
    return sql.format(filtered_column)


def add_wildcards(param):
    return '%' + param + '%'


def get_connection():
    return sqlite3.connect(DATABASE_FILE)
