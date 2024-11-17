# imports

from bs4 import BeautifulSoup
from datetime import datetime
from json import dumps, load
from os import path
from threading import Lock, get_ident
from util.season import get_season_entry, season_dir
from util.mongodb import *
from util.mount import *

# static var

anime_dir = "anime_data/"                                            # anime data directory path relative to util folder
anime_dir_lock = Lock()                                              # lock preventing two files from RW action to an anime file at the same time
datetime_format = "%m/%d/%Y %H:%M:%S"                                # format for the datetime variable
json_indent_len = 4                                                  # readable indent size

# functions

def get_anime_entry(anime_id : int,
                    anime_name : str, 
                    anime_url : str,
                    to_mongodb : bool,
                    thread_info_enabled : bool,
                    anime_data_path : str = anime_dir,) -> dict | None :
    """
    get_anime_entry -- This function will go through an anime page and retrieve
    information pertaining to the series.

    Arguments:
        anime_id -- Unique identifier used within the season entry
        anime_name -- Name of the anime
        anime_url -- URL pointing to the anime series
        to_mongodb -- When enabled it establishes connection to mongodb for
        storage; consult mongodb.py for mongodb implimentation
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging

    Keyword Arguments:
        anime_data_path -- This defines the destination the resultants are
        stored at ( default: anime_dir )

    Returns:
        The dictionary object of the anime series or NoneType Object in the
        case of error or something unforseen;
    """

    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running get_anime_entry')

    # grab data if it exists
    anime_dict = {}
    if not path.exists(anime_data_path + anime_id_to_file_name(anime_id)) :
        # establish connection
        content, retried, ret = init_session(anime_url,
                                             get_anime_entry,
                                             thread_info_enabled,
                                             args = [
                                                 anime_id,
                                                 anime_name, 
                                                 anime_url,
                                                 to_mongodb,
                                                 thread_info_enabled
                                             ],
                                             kwargs = {
                                                 'anime_data_path' : anime_data_path
                                             })

        # if the entire function needed a reset return the value finished with even if None
        if retried :
            return ret

        # initialize object
        anime_dict = {
            '_id' : anime_id,
            'name' : anime_name,
            'url' : anime_url
        }

        # grab data fields
        section_list_func = [
            get_anime_information_section,
            get_anime_synopsis_section,
        ]

        for func in section_list_func :
            func(anime_dict, BeautifulSoup(content, 'html.parser'))

        # traverse the character/staff fields as well
        char_dict, staff_dict = get_anime_character_staff_section(anime_url, thread_info_enabled)
        anime_dict['characters'] = char_dict
        anime_dict['staff'] = staff_dict
        
        # tries to write it to mongodb
        if to_mongodb :
            try :
                res = insert_doc_into_mongo(anime_dict,
                                            mongodb_database_name,
                                            mongodb_anime_collection,
                                            thread_info_enabled)
            except Exception as e :
                print(e)

        # write to disk
        with anime_dir_lock :
            with open(anime_data_path + anime_id_to_file_name(anime_id), 'w+') as file :
                file.write(dumps(anime_dict, indent=json_indent_len))
    else :
        # read the entry and return it
        with anime_dir_lock :
            with open(anime_data_path + anime_id_to_file_name(anime_id), 'r') as file :
                anime_dict = load(file)

    # return the season_dict
    return anime_dict

def anime_id_to_file_name(anime_id : int) -> str : 
    """
    anime_id_to_file_name : This function is a helper function make
    getting a file name more human readable.

    Arguments:
        anime_id -- The id of the anime as a string

    Returns:
        file name that should corispond to the season
    """
    return 'anime_' + str(anime_id) + ".json"

def get_anime_information_section(anime_dict : dict, soup : BeautifulSoup) -> None :
    """
    get_anime_information_section -- This function grabs most data from the
    information section.

    Arguments:
        anime_dict -- The dictionary containing the anime entry
        soup -- The response content from the session
    """
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

    # grab each field in info section
    info_section = soup.find_all('div', class_='spaceit_pad')
    for row in info_section :
        line = row.get_text(strip=True)
        idx = line.find(':')
        attr, value = line[:idx], line[idx+1:]
        anime_dict[attr.lower()] = value

def get_anime_synopsis_section(anime_dict : dict, soup : BeautifulSoup) -> None :
    """
    get_anime_synopsis_section -- This function grabs the synpopsis field from
    the page content.

    Arguments:
        anime_dict -- The dictionary containing the anime entry
        soup -- The response content from the session
    """
    synop = "".join([line.get_text(strip=True) for line in soup.find_all('p', itemprop='description')])
    anime_dict['synopsis'] = synop

def get_anime_character_staff_section(anime_url : str, thread_info_enabled : bool) -> tuple[dict, dict] :
    """
    get_anime_character_staff_section -- This function will grab the character
    and staff information from each entry and record the results in seperate
    dictionary objects.

    TODO: needs to be finished

    Arguments:
        anime_url -- The url that is connected to the anime entry
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging

    Returns:
        A tuple containing both the character and staff dictionaries.
    """
    # grab the content from the GET request
    content, retried, ret = init_session(anime_url + '/characters',
                                         get_anime_character_staff_section,
                                         thread_info_enabled,
                                         [anime_url + '/characters'])
    if retried :
        return ret
    
    # grab context for each section
    soup = BeautifulSoup(content, 'html.parser')
    character_ctx = soup.find_all('table', class_='js-anime-character-table')
    staff_ctx = soup.find_all('td', class_=['borderClass bgColor1', 'borderClass bgColor2'])

    # grab character information
    character_entries = {}
    for ctx in character_ctx :
        character_name = ctx.find('h3', class_='h3_character_name').text.strip()
        character_entries[character_name] = {}
        for atx in ctx.find_all('tr', class_='js-anime-character-va-lang') :
            actor_link = atx.find('a').get('href').strip()
            actor_name = atx.find('a').text.strip()
            actor_lang = atx.find('div', class_='spaceit_pad js-anime-character-language').text.strip()
            character_entries[character_name][actor_name] = {
                'link' : actor_link,
                'language' : actor_lang
            }
    
    # grab staff information
    staff_entries = {}
    for ctx in staff_ctx :
        staff_name = ctx.find('a').text.strip()
        staff_link = ctx.find('a').get('href').strip()
        staff_role = ctx.find('div', class_='spaceit_pad').text.strip()
        if staff_name != staff_role :
            staff_entries[staff_name] = {
                'link' : staff_link,
                'position' : staff_role
            }

    return (character_entries, staff_entries)
    