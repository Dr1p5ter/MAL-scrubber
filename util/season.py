# imports

from bs4 import BeautifulSoup
from bson import ObjectId, json_util
from datetime import datetime
from json import load
from os import path
from threading import Lock, get_ident
from util.mongodb import *
from util.mount import *
import util.tglob as tglob

# static var

mal_season_url = "https://myanimelist.net/anime/season/archive"      # MAL link for the seasonal anime archive page
season_file = '_season_list.csv'                                     # file to hold all season titles

# functions

def make_season_list_to_csv(skip_if_exists : bool = True,
                            thread_info_enabled : bool = False,
                            season_data_path : str = tglob.season_dir) -> int :    
    """
    make_season_list_to_csv -- Retrieves each season in the MAL archeive url
    and makes a file storing the names and urls associated for each season in
    a CSV file. This file will be stored in a subdirectory listed as
    season_data with the file name '_season_list.csv' for uniqueness.

    Keyword Arguments:
        skip_if_exists -- When the file is already present just return length
        of file and don't remake ( default: True )
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging ( default: False )
        season_data_path -- This defines the destinnation the resultants are
        stored at ( default: season_dir )

    Returns:
        Number of seasons grabbed from MAL; Doesn't get rid of entries with
        zero anime entries; intializes locks once read and should be grabbed
        before runtime of any function in library; Len of entries returned if
        path exists already;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running make_season_list_to_csv')

    # checks to see if it is already made
    if skip_if_exists and path.exists(season_data_path + season_file):
        with tglob.season_file_RW_lock :
            with open(season_data_path + season_file, 'r') as file :
                return len(file.readlines())

    # establish connection with MAL
    response, retried, ret = init_session(mal_season_url,
                                          make_season_list_to_csv,
                                          kwargs = {
                                              'skip_if_exists' : skip_if_exists,
                                              'thread_info_enabled' : thread_info_enabled,
                                              'season_data_path' : season_data_path
                                          })[2:]

    # if the entire function needed a reset return the value finished with even if None
    if retried :
        return ret

    # parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    soup = soup.find('table', attrs={'class' : 'anime-seasonal-byseason mt8 mb16'}).findAll()

    # for each season link, add it into the MAL csv
    seasons_grabbed = 0
    with tglob.season_file_RW_lock :
        with open(season_data_path + season_file, 'w+') as file :
            for tag in soup:
                if tag.name == 'a' :
                    key, value = str(tag.text).strip(), str(tag.get('href')).strip()               
                    file.write(f'{key}, {value}\n')
                    tglob.season_entry_RW_locks[key] = Lock()
                    seasons_grabbed += 1

    return  seasons_grabbed

def season_name_to_file_name_json(season_name : str) -> str : 
    """
    season_name_to_file_name_json : This function that makes the file name more
    human readable solely based on season_name.

    Arguments:
        season_name -- The name of the season as a string

    Returns:
        File name that should corispond to the season;
    """
    return season_name.lower().replace(' ', '_') + ".json"

def get_season_entry(season_name : str,
                     season_url : str,
                     to_mongodb : bool,
                     thread_info_enabled : bool = False,
                     season_data_path : str = tglob.season_dir) -> dict | None :
    """
    get_season_entry : This function will retrieve the seasons entry from the
    season data subdirectory or fetch it using an HTTP GET request.

    Arguments:
        season_name -- Name of the season
        season_url -- URL linking to the season in MyAnimeList.net
        to_mongodb -- When enabled it establishes connection to mongodb for
        storage

    Keyword Arguments:
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging ( default: False )
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
    if not path.exists(season_data_path + season_name_to_file_name_json(season_name)) :
        # establish connection with MAL
        response, retried, ret = init_session(season_url, 
                                              get_season_entry, 
                                              args = [
                                                  season_name,
                                                  season_url,
                                                  to_mongodb
                                              ],
                                              kwargs = {
                                                  'thread_info_enabled' : thread_info_enabled,
                                                  'season_data_path' : season_data_path
                                              })[2:]

        # if the entire function needed a reset return the value finished with even if None
        if retried :
            return ret

        # parse the content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # gets rid of tv continued page (potential redundent data)
        for div in soup.find_all("div", class_='seasonal-anime-list js-seasonal-anime-list js-seasonal-anime-list-key-1') :
            if "TV (Continuing)" in div.text :
                div.decompose()
        soup.prettify()

        # find all sections
        soup = soup.find_all('a', class_='link-title')

        # initialize the season_dict
        season_dict = {
            'season' : season_name.split(' ')[0].lower(),
            'year' : int(season_name.split(' ')[1]),
            'url' : season_url,
            'datetime_entered' : datetime.now().strftime(tglob.datetime_format),
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
                'name' : anime_name,
                'url' : anime_url,
                'datetime_entered' : datetime.now().strftime(tglob.datetime_format),
                'datetime_filled' : None,
            }

            # append it to the seasonal_anime tab
            season_dict["seasonal_anime"].append(anime_info)

        # check to see if there are anime series present in series
        num_anime_entries = len(season_dict['seasonal_anime'])
        if num_anime_entries < 1 :
            with tglob.season_file_RW_lock :
                # remove season from list aquired from archeives
                with open(season_data_path + season_file, 'r') as file : 
                    lines = [(line.split(', ')[0].strip(), line.split(', ')[1].strip()) for line in file.readlines()]
                    lines.remove((season_name, season_url))
            
                # update the list
                with open(season_data_path + season_file, 'w') as file:
                    for line in lines :
                        file.write(f'{line[0]}, {line[1]}\n')
            
            # get rid of the lock for that speciic season
            tglob.season_entry_RW_locks.pop(season_name)

            return None
        else :
            season_dict['total_anime_entries'] = num_anime_entries

        # write out the json as the season_name
        with tglob.season_entry_RW_locks[season_name] :
            # tries to write it to mongodb
            if to_mongodb :
                try :
                    object_id, res = insert_doc_into_mongo(season_dict,
                                                           mongodb_database_name,
                                                           mongodb_season_collection,
                                                           thread_info_enabled=thread_info_enabled)
                    if  res:
                        season_dict = grab_doc_from_mongo({'_id' : ObjectId(object_id)},
                                                        mongodb_database_name,
                                                        mongodb_season_collection,
                                                        thread_info_enabled=thread_info_enabled)
                except Exception as e :
                    print(e)
            
            # write to disk
            with open(season_data_path + season_name_to_file_name_json(season_name), 'w') as file :
                file.write(json_util.dumps(season_dict, indent=tglob.json_indent_len))
    else :
        with tglob.season_entry_RW_locks[season_name] :
            with open(season_data_path + season_name_to_file_name_json(season_name), 'r') as file :
                season_dict = load(file)

    # return the season_dict
    return season_dict