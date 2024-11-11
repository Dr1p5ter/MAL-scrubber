# imports

from datetime import datetime, timedelta
from os import path, stat, remove, mkdir, listdir
from util.anime import anime_dir
from util.season import archive_file, season_dir
from util.mongodb import drop_docs_in_collections

# remove the season data if it exists
if path.exists(season_dir) :
    init_start_last = datetime.fromtimestamp(stat(season_dir).st_birthtime)
    two_week_ahead = timedelta(days = 14)
    time_now = datetime.now()
    if (not path.exists(season_dir + archive_file)) or time_now > init_start_last + two_week_ahead:
        for file in listdir(season_dir) :
            remove(season_dir + file)
else :
    mkdir(season_dir)

# remove the anime data if it exists
if path.exists(anime_dir) :
    for file in listdir(anime_dir) :
        remove(anime_dir + file)
else :
    mkdir(anime_dir)

# clean all collections in mongodb
drop_docs_in_collections()