from concurrent.futures import ThreadPoolExecutor
from json import load
from os import listdir
from util.anime import *
from util.init import *
from util.season import *

# does nothing CRUD app
if __name__ == '__main__' :
    # make the csv of season names and urls from the archive
    make_archive_list_to_csv(True, True)
    
    # get data on every season and upload them to mongodb
    with open(season_dir + archive_file, 'r') as file :
        with ThreadPoolExecutor() as executor :
            [
                executor.submit(get_season_entry,
                                line.strip().split(', ')[0],
                                line.strip().split(', ')[1],
                                True,
                                True)
                for line in file.readlines()
            ]

    # go through each file in season_data and fill in anime data entries if
    # any are present
    for file in listdir(season_dir) :
        with open(season_dir + file, 'r') as file :
            season_entry = load(file)
            anime_entries = season_entry['seasonal_anime']
            with ThreadPoolExecutor() as executor :
                [
                    executor.submit(get_anime_entry,
                                    anime['_id'],
                                    anime['name'],
                                    anime['url'],
                                    True,
                                    True)
                    for anime in anime_entries]