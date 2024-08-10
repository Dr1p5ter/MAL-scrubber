# TODO: mess with concurrency later
# import concurrent.futures
# import threading

# full import
from helper import *

# specified imports
from bs4 import BeautifulSoup
from datetime import datetime
from hashlib import md5
from json import dumps, load as json_load
from os import path, remove as rm
from random import randint
from requests import get as req_get, Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RetryError
from time import time, sleep
from urllib3.util import Retry
from uuid import UUID

# url to search from (static)
MAL_url = "https://myanimelist.net/anime/season/archive"

# file to store season names and links if file wasn't made the same day
MAL_season_sheet = "MAL_season_links.csv"
archieve_dict = {}

backtrack_list_file_name = "season_backtrack.txt" # file for season backtracking
backtrack_list = []                               # list of completed season parsing

# directories for data
season_dir = "./season_data/"
anime_dir = "./anime_data/"

# anime data retrieval status codes
CODE_I = "INCOMPLETE"
CODE_C = "COMPLETE"
CODE_E = "ERROR"

# datetime format
dt_format = "%m/%d/%Y %H:%M:%S"

# indent length for json format
indent_len = 4

# pause intervals
pmin, pmax = 3, 30
pfactor = 0.1

# packet retry time
rtime = 3 * 60

# retry policy for each session
retry_strategy = Retry(
    total=3,
    backoff_factor=5,
    status_forcelist=[405, 429, 500, 502, 503, 504],
)

def generate_MAL_csv() -> None :
    """
    generate_MAL_csv -- This function creates a copy of all of
    the seasons and their respective links that hold all anime entries
    for that day. It is subject to change however, this should only be
    ran once a day typically.
    """
    try :
        # create an adaptor holding the retry policy
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # generate a session with the adapter
        session = Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # sent a GET request and raise for status changes other than success (200)
        response = session.get(MAL_url)
        response.raise_for_status()
    except RetryError as exception:
        # retry attempt if retry happens, this typically won't happen but needs to be handled
        print(f'{exception}')
        print(f'Error occured when session was attempting for packet retrieval, wait then retry aftr {rtime / 60} minutes')
        sleep(rtime)
        generate_MAL_csv()
        return

    # parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    soup = soup.find('table', attrs={'class' : 'anime-seasonal-byseason mt8 mb16'}).findAll()

    # for each season link, add it into the MAL csv
    with open(MAL_season_sheet, 'w') as file :
        for tag in soup:
            if tag.name == 'a' :
                key, value = str(tag.text).strip(), str(tag.get('href')).strip()
                archieve_dict[key] = value
                file.write(f'{key}, {value}\n')

    # set a generic timer to make sure packets aren't being sent to fast
    sleep(randint(pmin, pmax) * pfactor)
    
    return
    # generate_MAL_csv

def read_season_entry(season_name: str, season_url: str) -> None :
    """
    read_season_entry -- This function will go through a season page 
    and gather all anime entries for that season. This will be 
    recorded and progress saved through logs. In the event of a crash
    it will go back to the spot it stopped and will redo anything it
    didn't finish.

    Arguments:
        season_name -- The name of the season being read from.
        season_url -- The url being searched from.
    """
    # grab data if it exists
    season_dict = {}
    if not path.exists(season_dir + season_name_to_file_name(season_name)) :
        # TODO: extend this try block to handle keyboard exceptions and other cases since this seems to happen often
        try :
            # create an adaptor holding the retry policy
            adapter = HTTPAdapter(max_retries=retry_strategy)

            # generate a session with the adapter
            session = Session()
            session.mount('http://', adapter)
            session.mount('https://', adapter)

            # sent a GET request and raise for status changes other than success (200)
            response = session.get(season_url)
            response.raise_for_status()
        except RetryError as exception:
            # restart the entire season if a response error occurs
            print(f'{exception}')
            print(f'Error occured when session was attempting for packet retrieval, wait then retry aftr {rtime / 60} minutes')
            sleep(rtime)
            read_season_entry(season_name, season_url)
            return

        # parse the content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # parse the content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # gets rid of tv continued page (potential redundent data)
        for div in soup.find_all("div", class_='seasonal-anime-list js-seasonal-anime-list js-seasonal-anime-list-key-1') :
            if "TV (Continuing)" in div.text :
                div.decompose()
        soup.prettify()

        # find all sections
        soup = soup.find_all('a', class_='link-title')

        # iterate through each section
        season_dict = {
            '_id_' : md5(season_name.encode("UTF-8")).hexdigest(),
            'season' : season_name.split(' ')[0].lower(),
            'year' : int(season_name.split(' ')[1]),
            'url' : season_url,
            'seasonal_anime' : []
        }
        for a in soup:
            # grab basic series information
            anime_name = str(a.text).strip()
            anime_url = str(a.get('href')).strip()
            anime_id = anime_name_to_id(anime_name)

            # place the information into a dictionary
            anime_info = {}
            anime_info['anime_id'] = anime_id
            anime_info['name'] = anime_name
            anime_info['url'] = anime_url
            anime_info['loaded_in_directory'] = CODE_I
            anime_info['datetime_entered'] = datetime.now().strftime(dt_format)
            anime_info['datetime_completed'] = None

            # append it to the seasonal_anime tab
            season_dict["seasonal_anime"].append(anime_info)

        # write out the json as the season_name
        with open(season_dir + season_name_to_file_name(season_name), 'w') as file :
            file.write(dumps(season_dict, indent=4))
    else :
        with open(season_dir + season_name_to_file_name(season_name), 'r') as file :
            season_dict = json_load(file)

    # go through each anime and grab the data
    anime_files = season_dict["seasonal_anime"]
    for anime in anime_files :
        # check if the anime has already been loaded
        if (anime["loaded_in_directory"] == CODE_C) and (path.exists(anime_dir + anime['anime_id'] + ".json")):
            continue
        
        # read the anime entry
        try :
            # on completed data retrieval modify log for entry
            read_anime_entry(anime["name"], anime["url"])
            anime["loaded_in_directory"] = CODE_C
            anime["datetime_completed"] = datetime.now().strftime(dt_format)
        except Exception as exception:
            # if any case where exception wasn't totally known (skipped but recorded as ERROR)
            anime["loaded_in_directory"] = CODE_E
            print(exception)
            print(f'{anime} must be tried at a later date')
        except KeyboardInterrupt :
            # if a case where console interuption is necessary to halt process this will ensure code goes in as ERROR
            print(f'Keyboard interrupt has occured, data retrieval will go in as error for this entry and will be completed at a later date:')
            print(f'{anime} must be tried at a later date')
            anime["loaded_in_directory"] = CODE_E
            with open(season_dir + season_name_to_file_name(season_name), 'w') as file :
                file.write(dumps(season_dict, indent=indent_len))
            
            # exit on error
            exit(-1)
        finally :
            # ensure write goes through for each case attempted/complete
            try :
                # try writing to season file
                with open(season_dir + season_name_to_file_name(season_name), 'w') as file :
                    file.write(dumps(season_dict, indent=indent_len))
            except KeyboardInterrupt :
                # in case of keyboard interrupt during this period file is still updated then exit
                with open(season_dir + season_name_to_file_name(season_name), 'w') as file :
                    file.write(dumps(season_dict, indent=indent_len))
                
                # exit on error
                exit(-1)

    # validate if season is fully completed
    code_dict = resultant_dict([anime['loaded_in_directory'] for anime in anime_files])
    if (code_dict[CODE_E] == 0) and (code_dict[CODE_I] == 0) :
        try :
            with open(backtrack_list_file_name, 'a') as file :
                file.write(season_name + '\n')
        except :
            print("force attempt had occured to write season into backtrack file, immediate force exit on error")
            exit(-1)

    return
    # read_season_entry()

def read_anime_entry(anime_name: str, anime_url: str) -> None :
    """
    read_anime_entry -- This function will go through an anime entry
    and grab information regarding the series. This will be collected
    depending on the season first, no other web links will be visited
    during the collection period. The information will be stored in a
    JSON file as the anime_name parameter.

    Arguments:
        anime_name -- name of the anime (season independent).
        anime_url -- url of the anime series.
    """
    try :
        # create an adaptor holding the retry policy
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # generate a session with the adapter
        session = Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # sent a GET request and raise for status changes other than success (200)
        response = session.get(anime_url)
        response.raise_for_status()
    except RetryError as exception:
        print(f'{exception}')
        print(f'Error occured when session was attempting for packet retrieval, wait then retry aftr {rtime / 60} minutes')
        sleep(rtime)
        raise Exception("RetryError occured within the session, retry this entry at a later date")

    # parse the content with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # gets rid of spans
    for span in soup.find_all("span", style='display: none') :
        span.decompose()
    soup.prettify()

    # gets rid of sups
    for sup in soup.find_all("sup") :
        sup.decompose()
    soup.prettify()

    # gets rid of ranked subtext
    for div in soup.find_all("div", class_=['statistics-info info1', 'statistics-info info2']) :
        div.decompose()
    soup.prettify()

    # getting rid of character details
    for td in soup.find_all("td", class_='pb24') :
        td.decompose()
    soup.prettify()

    # find the Information section
    info_section = soup.find_all('div', class_='spaceit_pad')

    # loop through each item in the Information section
    entry = {}
    entry['_id_'] = anime_name_to_id(anime_name)
    entry['name'] = anime_name
    entry['url'] = anime_url
    for row in info_section :
        line = row.get_text(strip=True)
        idx = line.find(':')
        attr, value = line[:idx], line[idx+1:]
        entry[attr.lower()] = value
    
    # grab synopsis and add to entry
    synop = "".join([line.get_text(strip=True) for line in BeautifulSoup(response.content, 'html.parser').find_all('p', itemprop='description')])
    entry['synopsis'] = synop

    # write the data to a file
    with open(anime_dir + entry['_id_'] + '.json', 'w') as file :
        file.write(dumps(entry, indent=indent_len))
    
    # set a generic timer to make sure packets aren't being sent to fast
    sleep(randint(pmin, pmax) * pfactor)

    return
    # read_anime_entry

# begin main block of code
if __name__ == '__main__' :

    # check if the file exists and if it was made today
    if not path.exists(MAL_season_sheet) :
        # generate the file since it doesn't exist
        generate_MAL_csv()
        clean_data_dir()
        clean_backtrack_data()
    else :
        try :
            # read from MAL file
            with open(MAL_season_sheet, 'r') as file :
                for line in file.readlines() :
                    key, value = line.rstrip().split(', ')
                    archieve_dict[key] = value
        except Exception as e :
            print(e)
            exit(-1)

    # continuously go through each season until they are all read in
    while True :
        # go key by key in the archieve dict
        for key in archieve_dict.keys() :
            # if it is not in the backtrack_list read the season
            if not key in open(backtrack_list_file_name, 'r').readlines() :
                read_season_entry(key, archieve_dict[key])
        
        # check if each season has been read through
        if len(open(MAL_season_sheet, 'r').readlines()) == len(open(backtrack_list_file_name, 'r').readlines()) :
            # ends program
            break
        else :
            # continues the loop until each entry has been read in
            continue

    # exit on success
    exit(0)

    # main