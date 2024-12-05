# imports

import argparse

# parser for grabbing settings needed for storing data
p = argparse.ArgumentParser()
p.add_argument('-t', '--threadinfo', help='enable thread info in terminal upon calls', action='store_true')
p.add_argument('-m', '--mongodb', help='enable mongodb connection (no disk writing)', action='store_true')
args = p.parse_args()

# app
if __name__ == '__main__' :
    # local imports
    from concurrent.futures import ThreadPoolExecutor
    from json import load
    from os import listdir
    from util.anime import get_anime_entry
    from util.init import *
    from util.mongodb import generate_cursor, mongodb_database_name, mongodb_season_collection
    from util.season import get_season_entry, make_archive_list_to_csv, archive_file, season_dir

    # make the csv of season names and urls from the archive
    make_archive_list_to_csv(True, args.threadinfo)
    
    # get data on every season and upload them to mongodb
    with open(season_dir + archive_file, 'r') as file :
        with ThreadPoolExecutor() as executor :
            [
                executor.submit(get_season_entry,
                                line.strip().split(', ')[0],
                                line.strip().split(', ')[1],
                                args.threadinfo,
                                args.mongodb)
                for line in file.readlines()
            ]

    # go through each file in season_data and fill in anime data entries if any are present
    if args.mongodb :
        season_cursor = generate_cursor(mongodb_database_name,
                                        mongodb_season_collection,
                                        args.threadinfo)
        for season_entry in season_cursor :
            anime_entries = season_entry['seasonal_anime']
            with ThreadPoolExecutor() as executor :
                [
                    executor.submit(get_anime_entry,
                                    anime['_id'],
                                    anime['name'],
                                    anime['url'],
                                    args.threadinfo,
                                    args.mongodb)
                    for anime in anime_entries]
    else :
        for file in listdir(season_dir) :
            # skip the archive file since it is not in json format
            if file == archive_file :
                continue

            # grab the season entry
            season_entry = {}
            with open(season_dir + file, 'r') as fp :
                season_entry = load(fp)

            # generate a pool of threads to fill in anime data
            anime_entries = season_entry['seasonal_anime']
            with ThreadPoolExecutor() as executor :
                [
                    executor.submit(get_anime_entry,
                                    anime['_id'],
                                    anime['name'],
                                    anime['url'],
                                    args.threadinfo,
                                    args.mongodb)
                    for anime in anime_entries]
    exit(0)