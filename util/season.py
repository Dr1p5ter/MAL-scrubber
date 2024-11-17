# imports

from bs4 import BeautifulSoup
from datetime import datetime
from hashlib import sha256
from json import dumps, load
from os import path
from threading import Lock, get_ident
from util.mongodb import *
from util.mount import *

# static var

archive_file = 'archeive_list.csv'                                   # file to hold all season titles
archive_url = "https://myanimelist.net/anime/season/archive"         # MAL link for the seasonal anime archive page
datetime_format = "%m/%d/%Y %H:%M:%S"                                # format for the datetime variable
json_indent_len = 4                                                  # readable indent size
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

    # grab data if it exists
    season_dict = {}
    if not path.exists(season_data_path + season_name_to_file_name(season_name)) :
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

        # initialize the season_dict
        season_dict = {
            '_id' : get_season_id(),
            'season' : season_name.split(' ')[0].lower(),
            'year' : int(season_name.split(' ')[1]),
            'url' : season_url,
            'datetime_entered' : datetime.now().strftime(datetime_format),
            'datetime_filled' : None,
            'all_anime_entries_filled' : False,
            'total_anime_entries' : 0,
            'seasonal_anime' : [],
        }

        # fill in basic anime entry information (not actually populating with data)
        for a in soup:
            # grab basic series information
            anime_name = str(a.text).strip()
            anime_url = str(a.get('href')).strip()

            # place the information into a dictionary
            anime_info = {
                '_id' : get_anime_id(),
                'name' : anime_name,
                'url' : anime_url
            }

            # append it to the seasonal_anime tab
            season_dict["seasonal_anime"].append(anime_info)

        # check to see if there are anime series present in series
        num_anime_entries = len(season_dict['seasonal_anime'])
        if num_anime_entries < 1 :
            season_dict['all_anime_entries_filled'] = True
            season_dict['datetime_filled'] = datetime.now().strftime(datetime_format)
        else :
            season_dict['total_anime_entries'] = num_anime_entries
        season_dict['total_anime_entries'] = num_anime_entries

        # write out the json as the season_name
        if to_mongodb :
            try :
                insert_doc_into_mongo(season_dict,
                                      mongodb_database_name,
                                      mongodb_season_collection,
                                      thread_info_enabled)
            except Exception as e :
                print(e)
            
        # write to disk
        with season_dir_lock :
            with open(season_data_path + season_name_to_file_name(season_name), 'w') as file :
                file.write(dumps(season_dict, indent=json_indent_len))
    else :
        with season_dir_lock :
            with open(season_data_path + season_name_to_file_name(season_name), 'r') as file :
                season_dict = load(file)

    # return the season_dict
    return season_dict

def update_season_entry_to_disk(season_entry : dict) -> None :
    with season_dir_lock :
        with open(season_dir + season_name_to_file_name(season_entry['season'] + ' ' + str(season_entry['year'])), 'w') as file :
            file.write(dumps(season_entry, indent=json_indent_len))