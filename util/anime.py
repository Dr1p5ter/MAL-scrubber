# imports

from bs4 import BeautifulSoup
from json import dumps, load
from os import path
from threading import Lock, get_ident
from util.datenow import get_datetime_now
from util.jsonformat import json_indent_len
from util.mongodb import update_doc_in_mongo, insert_doc_into_mongo, grab_doc_from_mongo, mongodb_anime_collection, mongodb_database_name
from util.mount import *

# static var

anime_dir = "anime_data/"                                            # anime data directory path relative to util folder
anime_dir_lock = Lock()                                              # lock preventing two files from RW action to an anime file at the same time
info_not_found_str_regex = 'None found,add some'                     # regex for locating field values to not be split (looks weird)

# functions

def get_anime_entry(anime_id : int,
                    to_mongodb : bool,
                    thread_info_enabled : bool,
                    anime_data_path : str = anime_dir,) -> dict | None :
    """
    get_anime_entry -- This function will go through an anime page and retrieve
    information pertaining to the series.

    Arguments:
        anime_id -- Unique identifier used within the season entry
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

    # grab document from disk or mongodb :
    anime_entry : dict = {}
    if to_mongodb :
        anime_entry = grab_doc_from_mongo({'_id' : anime_id},
                                            mongodb_database_name,
                                            mongodb_anime_collection,
                                            thread_info_enabled)
    else :
        with anime_dir_lock :
            with open(anime_data_path + anime_id_to_file_name(anime_id), 'r') as file :
                anime_entry = load(file)
    
    # make sure the entry is not of NoneTime
    if anime_entry == None :
        anime_entry = {}

    # make sure that the entry wasn't already filled
    if anime_entry.get('datetime_filled', None) == None :
        # establish connection
        content, retried, ret = init_session(anime_entry['url'],
                                            get_anime_entry,
                                            thread_info_enabled,
                                            args = [
                                                anime_id,
                                                to_mongodb,
                                                thread_info_enabled
                                            ],
                                            kwargs = {
                                                'anime_data_path' : anime_data_path
                                            })

        # if the entire function needed a reset return the value finished with even if None
        if retried :
            return ret
        
        # grab data fields
        section_list_func = [
            get_anime_information_section,
            get_anime_synopsis_section,
        ]
        for func in section_list_func :
            func(anime_entry, BeautifulSoup(content, 'html.parser'))

        # traverse the character/staff fields as well
        char_dict, staff_dict = get_anime_character_staff_section(anime_entry['url'], thread_info_enabled)
        if char_dict != None :
            anime_entry['characters'] = char_dict
        if staff_dict != None :
            anime_entry['staff'] = staff_dict

        # modify the filled datetime filled
        anime_entry['datetime_filled'] = get_datetime_now()

        # tries to update document it to mongodb
        if to_mongodb :
            try :
                update_doc_in_mongo({'_id' : anime_id},
                                    anime_entry,
                                    mongodb_database_name,
                                    mongodb_anime_collection,
                                    thread_info_enabled)
            except Exception as e :
                print(f'Exception in get_anime_entry() during replacement : {e}\nanime_id : {anime_id}')
                return None

        # write to disk
        with anime_dir_lock :
            with open(anime_data_path + anime_id_to_file_name(anime_id), 'w+') as file :
                file.write(dumps(anime_entry, indent=json_indent_len))
    
    # return the entry
    return anime_entry

def init_anime_entry(anime_entry : dict,
                     thread_info_enabled : bool,
                     to_mongodb : bool,
                     anime_data_path : str = anime_dir) -> None :
    """
    init_anime_entry : This function will initialize documents depending on the
    setting selected for mongodb.

    Arguments:
        anime_entry -- Document to be inserted
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging
        to_mongodb -- When enabled it establishes connection to mongodb for
        storage

    Keyword Arguments:
        anime_data_path -- This defines the destination the resultants are
        stored at ( default: anime_dir )
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running init_anime_entry')
    
    # write to disk or to mongodb
    if to_mongodb :
        insert_doc_into_mongo(anime_entry,
                              mongodb_database_name,
                              mongodb_anime_collection,
                              thread_info_enabled)
    else :
        with anime_dir_lock:
            with open(anime_data_path + anime_id_to_file_name(anime_entry['_id']), 'w') as file :
                file.write(dumps(anime_entry))

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
    info_soup = soup.find('div', class_='leftside')
    info_soup = info_soup.find_all('div', class_='spaceit_pad')
    for row in info_soup :
        line = row.get_text(strip=True)
        idx = line.find(':')
        if idx > 0  and line[-1] != ':':
            attr, values = line[:idx], line[idx+1:]
            if values.find(',') < len(values) and values.strip() != info_not_found_str_regex:
                if values.find(',') > 0  and values[values.find(',') + 1].isalpha() :
                    values = [v.strip() for v in values.split(',')]
            anime_dict[attr.lower()] = values

def get_anime_synopsis_section(anime_dict : dict, soup : BeautifulSoup) -> None :
    """
    get_anime_synopsis_section -- This function grabs the synpopsis field from
    the page content.

    Arguments:
        anime_dict -- The dictionary containing the anime entry
        soup -- The response content from the session
    """
    try :
        synop = "".join([line.get_text(strip=True) for line in soup.find_all('p', itemprop='description')])
        anime_dict['synopsis'] = synop
    except AttributeError as e :
        print(f'Exception {e.name} has occured with URL {anime_dict['url']} [entry possibly has fewer attributes or has none]')
        print(f'{e}')

def get_anime_character_staff_section(anime_url : str, thread_info_enabled : bool) -> tuple[dict, dict] :
    """
    get_anime_character_staff_section -- This function will grab the character
    and staff information from each entry and record the results in seperate
    dictionary objects.

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

    # grab character information
    character_entries = {}
    try :
        # grab the character_soup
        character_soup = soup.find('div', class_='anime-character-container js-anime-character-container')
        character_soup = character_soup.find_all('table', class_='js-anime-character-table')

        # go through the table elements and attempt to parse the character data
        for table in character_soup :
            character_name = table.find('h3', class_='h3_character_name').text.strip()
            character_favorites = table.find('div', class_='js-anime-character-favorites').text.strip()
            character_entries[character_name] = {
                'favorites' : character_favorites,
                'actors' : []
            }
            for tr in table.find_all('tr', class_='js-anime-character-va-lang') :
                td = tr.find('td', attrs={'align' : 'right', 'style' : 'padding: 0 4px;', 'valign' : 'top'})
                actor_entry = {
                    'name' : td.find('a').text.strip(),
                    'language' : td.find('div', class_='js-anime-character-language').text.strip(),
                    'link' : td.find('a').get('href').strip()
                }
                character_entries[character_name]['actors'].append(actor_entry)
    except AttributeError as e :
        print(f'Exception {e.name} has occured with URL {anime_url} [entry possibly has fewer attributes or has none]')
        print(f'{e}')
    finally :
        if len(character_entries.keys()) < 1 :
            character_entries = None

    # grab staff information
    staff_entries = {}
    try :
        staff_soup = soup.find('div', class_='rightside js-scrollfix-bottom-rel')
        staff_soup = staff_soup.find_all('table', class_=None)
        for table in staff_soup :
            td = table.find('td', attrs={'width' : None})
            staff_name = td.find('a').text.strip()
            staff_link = td.find('a').get('href').strip()
            staff_roles = td.find('div', class_='spaceit_pad').text.strip()
            if staff_roles.find(',') > 0 :
                staff_roles = staff_roles.split(', ')
            staff_entries[staff_name] = {
                'roles' : staff_roles,
                'link' : staff_link
            }
    except AttributeError as e :
        print(f'Exception {e.name} has occured with URL {anime_url} [entry possibly has fewer attributes or has none]')
        print(f'{e}')
    finally :
        if len(staff_entries.keys()) < 1 :
            staff_entries = None

    return (character_entries, staff_entries)
    