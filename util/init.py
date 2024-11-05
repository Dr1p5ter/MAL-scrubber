# imports

from datetime import datetime, timedelta
from os import path, stat, remove, mkdir, listdir
from util.season import season_file
import util.tglob as tglob

# remove the season data if it exists
if path.exists(tglob.season_dir) :
    init_start_last = datetime.fromtimestamp(stat(tglob.season_dir + season_file).st_birthtime)
    two_week_ahead = timedelta(days = 14)
    time_now = datetime.now()
    if (not path.exists(tglob.season_dir + season_file)) or time_now > init_start_last + two_week_ahead:
        for file in listdir(tglob.season_dir) :
            remove(tglob.season_dir + file)
else :
    mkdir(tglob.season_dir)

# remove the anime data if it exists
if path.exists(tglob.anime_dir) :
    for file in listdir(tglob.anime_dir) :
        remove(tglob.anime_dir + file)
else :
    mkdir(tglob.anime_dir)