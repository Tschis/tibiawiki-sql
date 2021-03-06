# tibiawiki-sql [![Build Status](https://travis-ci.org/Galarzaa90/tibiawiki-sql.svg?branch=master)](https://travis-ci.org/Galarzaa90/tibiawiki-sql) ![Python](https://img.shields.io/badge/python-3.6+-yellow.svg) [![GitHub (pre-)release](https://img.shields.io/github/release/Galarzaa90/tibiawiki-sql/all.svg)](https://github.com/Galarzaa90/tibiawiki-sql/releases) 
Script that generates a sqlite database for the MMO Tibia.

Inspired in [Mytherin's Tibiaylzer](https://github.com/Mytherin/Tibialyzer) TibiaWiki parsing script.

This script fetches data from TibiaWiki via its API, compared to relying on [database dumps](http://tibia.wikia.com/wiki/Special:Statistics)
that are not updated as frequently. By using the API, the data obtained is always fresh.

This script is not intended to be running constantly, it is meant to be run once, generate a sqlite database and use it 
externally.

## Requirements

* Python 3.6 or higher
    * **requests** module
    
## Running the script
To execute the script, run `tibiawiki-sql.py`.

The process can be long, taking up to 20 minutes the first time. All images are saved to the `images` folder. On 
subsequent runs, images will be read from disk instead of being fetched from TibiaWiki again.

When done, a database file called `tibia_database.db` will be found on the folder.

## Database contents
* Creatures
* Items
* Creature drop statistics
* NPCs
* NPC offers
* Spells
* Houses
* Achievements
* Quests

## Database schema
See [SCHEMA.md](docs/SCHEMA.md) in the `docs` folder

## Contributing
Improvements and bug fixes are welcome, via pull requests  
For questions, suggestions and bug reports, submit an issue.

The best way to contribute to this project is by contributing to [TibiaWiki](http://tibia.wikia.com)

