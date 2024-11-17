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
        # skip the archive file since it is not in json format
        if file == archive_file :
            continue

        # grab the season entry
        season_entry = {}
        with open(season_dir + file, 'r') as fp :
            season_entry = load(fp)

        # generate a pool of threads to fill in anime data
        if not season_entry['all_anime_entries_filled'] :
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
                
            # update the season information and write it 
            season_entry['datetime_filled'] = datetime.now().strftime(datetime_format)
            season_entry['all_anime_entries_filled'] = True

            # update this to disk
            update_season_entry_to_disk(season_entry)

            # update this to mongodb
            update_doc_in_mongo({'_id' : season_entry['_id']},
                                season_entry,
                                mongodb_database_name,
                                mongodb_season_collection,
                                True)