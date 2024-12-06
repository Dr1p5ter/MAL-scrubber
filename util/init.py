# imports

from os import path, remove, mkdir, listdir
from util.anime import anime_dir
from util.season import season_dir
from util.mongodb import drop_docs_in_collection, mongodb_season_collection, mongodb_anime_collection, mongodb_anime_ids_serialized

# static var

util_dir = 'util/'

# remove the season data if it exists
if path.exists(season_dir) :
    for file in listdir(season_dir) :
        remove(season_dir + file)
else :
    mkdir(season_dir)
drop_docs_in_collection(mongodb_season_collection)

# remove the anime data if it exists
if path.exists(anime_dir) :
    for file in listdir(anime_dir) :
        remove(anime_dir + file)
else :
    mkdir(anime_dir)
drop_docs_in_collection(mongodb_anime_collection)

# check if pkl file is there and if it is remove it
if path.exists(util_dir + mongodb_anime_ids_serialized) :
    remove(util_dir + mongodb_anime_ids_serialized)