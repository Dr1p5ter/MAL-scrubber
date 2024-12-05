# imports

from bs4 import BeautifulSoup
from json import dumps, load
from os import path
from threading import Lock, get_ident
from util.anime import init_anime_entry
from util.datenow import get_datetime_now
from util.jsonformat import json_indent_len
from util.mongodb import get_anime_id, get_season_id, mongodb_season_collection, mongodb_database_name, insert_doc_into_mongo, grab_doc_from_mongo
from util.mount import *

# static var

archive_file = 'archeive_list.csv'                                   # file to hold all season titles
archive_url = "https://myanimelist.net/anime/season/archive"         # MAL link for the seasonal anime archive page
season_dir = "season_data/"                                          # seasonal data directory path relative to util folder
season_dir_lock = Lock()                                             # lock preventing two files from RW action to a season file at the same time

# functions

def make_archive_list_to_csv(skip_if_exists : bool,
                             thread_info_enabled : bool,
                             archive_list_path : str = season_dir) -> int :
    """
    make_archive_list_to_csv -- Retrieves each season in the MAL archeive url
    and makes a file storing the names and urls associated for each season in
    a CSV file. This file will be stored in a subdirectory listed as
    season_data with the file name 'archeive_list.csv' for uniqueness.

    Arguments :
    skip_if_exists -- When the file is already present just return length
    of file and don't remake
    thread_info_enabled -- When threads are implimented this will allow a
    print statement for debugging

    Keyword Arguments:
        archive_list_path -- This defines the destinnation the resultants are
        stored at ( default: season_dir )

    Returns:
        Number of seasons grabbed from MAL; Doesn't get rid of entries with
        zero anime entries; intializes locks once read and should be grabbed
        before runtime of any function in library; Len of entries returned if
        path exists already;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running make_archive_list_to_csv')

    # checks to see if it is already made
    if skip_if_exists and path.exists(archive_list_path + archive_file):
        num_of_seasons = 0
        with open(archive_list_path + archive_file, 'r') as file :
            num_of_seasons = len(file.readlines())
        return num_of_seasons

    # establish connection with MAL
    content, retried, ret = init_session(archive_url,
                                         make_archive_list_to_csv,
                                         thread_info_enabled,
                                         args=[
                                             skip_if_exists,
                                             thread_info_enabled
                                         ],
                                         kwargs = {
                                             'archive_list_path' : archive_list_path
                                         })

    # if the entire function needed a reset return the value finished with even if None
    if retried :
        return ret

    # parse the content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    soup = soup.find('table', attrs={'class' : 'anime-seasonal-byseason mt8 mb16'}).findAll()

    # for each season link, add it into the MAL csv
    seasons_grabbed = 0
    with open(archive_list_path + archive_file, 'w+') as file :
        for tag in soup:
            if tag.name == 'a' :
                key, value = str(tag.text).strip(), str(tag.get('href')).strip()               
                file.write(f'{key}, {value}\n')
                seasons_grabbed += 1

    return  seasons_grabbed

def season_name_to_file_name(season_name : str) -> str : 
    """
    season_name_to_file_name : This function that makes the file name more
    human readable solely based on season_name.

    Arguments:
        season_name -- The name of the season as a string

    Returns:
        File name that should corispond to the season with .json extender;
    """
    return season_name.lower().replace(' ', '_') + ".json"

def get_season_entry(season_name : str,
                     season_url : str,
                     thread_info_enabled : bool,
                     to_mongodb : bool,
                     season_data_path : str = season_dir) -> dict | None :
    """
    get_season_entry : This function will retrieve the seasons entry from the
    season data subdirectory or fetch it using an HTTP GET request.

    Arguments:
        season_name -- Name of the season
        season_url -- URL linking to the season in MyAnimeList.net
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging
        to_mongodb -- When enabled it establishes connection to mongodb for
        storage

    Keyword Arguments:
        season_data_path -- This defines the destination the resultants are
        stored at ( default: season_dir )

    Returns:
        The dictionary object of the season or NoneType Object in the case of
        season deletion from _season_list.csv;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running get_season_entry')

    # grab document from disk or mongodb :
    season_entry : dict = {}
    if to_mongodb :
        season_entry = grab_doc_from_mongo({'url' : season_url},
                                            mongodb_database_name,
                                            mongodb_season_collection,
                                            thread_info_enabled)
    else :
        with season_dir_lock :
            with open(season_data_path + season_name_to_file_name(season_name), 'r') as file :
                season_entry = load(file)

    # make sure the entry is not of NoneTime
    if season_entry == None :
        season_entry = {}

    # grab data if it exists
    if season_entry.get('datetime_filled', None) == None :
        # establish connection with MAL
        content, retried, ret = init_session(season_url, 
                                              get_season_entry, 
                                              thread_info_enabled,
                                              args = [
                                                  season_name,
                                                  season_url,
                                                  thread_info_enabled,
                                                  to_mongodb,
                                              ],
                                              kwargs = {
                                                  'season_data_path' : season_data_path
                                              },)

        # if the entire function needed a reset return the value finished with even if None
        if retried :
            return ret

        # parse the content with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')

        # gets rid of tv continued page (potential redundent data)
        for div in soup.find_all("div", class_='seasonal-anime-list js-seasonal-anime-list js-seasonal-anime-list-key-1') :
            if "TV (Continuing)" in div.text :
                div.decompose()
        soup.prettify()

        # find all sections
        soup = soup.find_all('a', class_='link-title')

        # initialize the season_entry
        season_entry = {
            '_id' : get_season_id(),
            'season' : season_name.split(' ')[0].lower(),
            'year' : int(season_name.split(' ')[1]),
            'url' : season_url,
            'datetime_entered' : get_datetime_now(),
            'datetime_filled' : None,
            'total_anime_entries' : 0,
            'seasonal_anime' : [],
        }

        # fill in basic anime entry information (not actually populating with data)
        for a in soup:
            # grab basic series information
            anime_name = str(a.text).strip()
            anime_url = str(a.get('href')).strip()

            # place the information into a dictionary
            anime_entry = {
                '_id' : get_anime_id(),
                'name' : anime_name,
                'url' : anime_url,
                'season' : season_name.split(' ')[0].lower(),
                'year' : int(season_name.split(' ')[1]),
                'datetime_entered' : get_datetime_now(),
                'datetime_filled' : None
            }

            # initialize document
            init_anime_entry(anime_entry,
                             thread_info_enabled,
                             to_mongodb)

            # get rid of the redundant information for the season entry
            anime_entry.pop('url')
            anime_entry.pop('season')
            anime_entry.pop('year')
            anime_entry.pop('datetime_entered')
            anime_entry.pop('datetime_filled')

            # append it to the seasonal_anime tab
            season_entry["seasonal_anime"].append(anime_entry)

        # check to see if there are anime series present in series
        season_entry['total_anime_entries'] = len(season_entry['seasonal_anime'])
        season_entry['datetime_filled'] = get_datetime_now()

        # write out the json as the season_name
        if to_mongodb :
            insert_doc_into_mongo(season_entry,
                                    mongodb_database_name,
                                    mongodb_season_collection,
                                    thread_info_enabled)
        else :
            # write to disk
            with season_dir_lock :
                with open(season_data_path + season_name_to_file_name(season_name), 'w') as file :
                    file.write(dumps(season_entry, indent=json_indent_len))

    # return the season_entry
    return season_entry
