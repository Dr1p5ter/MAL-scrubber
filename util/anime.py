# imports

from bs4 import BeautifulSoup
from datetime import datetime
from hashlib import md5
from json import dumps, load
from os import path
from threading import Lock, get_ident
from util.season import season_dir, get_season_entry, season_name_to_file_name_json
from util.mongodb import *
from util.mount import *
from util.tglob import *

# functions

def get_anime_entry(anime_name : str, 
                    anime_url : str,
                    season_name : str,
                    season_url : str,
                    to_mongodb : bool,
                    thread_info_enabled : bool = False,
                    anime_data_path : str = anime_dir,
                    season_data_path : str = season_dir) -> dict | None :
    """
    get_anime_entry -- This function will go through an anime page and retrieve
    information pertaining to the series.

    Arguments:
        anime_name -- Name of the anime
        anime_url -- URL pointing to the anime series
        season_name -- Name of the season corrilating to the anime series
        season_url -- URL pointint to the season the anime is a part of
        to_mongodb -- When enabled it establishes connection to mongodb for
        storage; consult mongodb.py for mongodb implimentation;

    Keyword Arguments:
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging ( default: False )
        anime_data_path -- This defines the destination the resultants are
        stored at ( default: anime_dir )
        season_data_path -- This defines the destination the resultants are
        stored at ( default: season_dir )

    Returns:
        The dictionary object of the anime series or NoneType Object in the
        case of error or something unforseen;
    """

    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running get_anime_entry')

    # grab data if it exists
    anime_dict = {}
    if not path.exists(anime_data_path + anime_name_to_file_name_json(anime_name)) :
        # establish connection
        response, retried, ret = init_session(anime_url,
                                              get_anime_entry,
                                              args = [
                                                  anime_name, 
                                                  anime_url,
                                                  season_name,
                                                  season_url
                                              ],
                                              kwargs = {
                                                  'thread_info_enabled' : thread_info_enabled,
                                                  'anime_data_path' : anime_data_path,
                                                  'season_data_path' : season_data_path
                                              })[2:]

        # if the entire function needed a reset return the value finished with even if None
        if retried :
            return ret

        # initialize object
        anime_dict = {
            'name' : anime_name,
            'url' : anime_url
        }

        # grab data fields
        section_list_func = [
            get_anime_information_section,
            get_anime_synopsis_section,
            get_anime_background_section,
        ]
        for func in section_list_func :
            func(anime_dict, BeautifulSoup(response.content, 'html.parser'))

        # TODO: finish the character/staff parsing
        # traverse the character/staff fields as well
        # char_dict, staff_dict = get_anime_character_staff_section(anime_url)
        # anime_dict['characters'] = char_dict
        # anime_dict['staff'] = staff_dict

        # write the data to a file and update season file
        with season_entry_RW_locks[season_name] :
            # tries to write it to mongodb
            if to_mongodb :
                try :
                    anime_object_id, res = insert_doc_into_mongo(anime_dict,
                                                           mongodb_database_name,
                                                           mongodb_anime_collection,
                                                           thread_info_enabled=thread_info_enabled)
                    if res :
                        anime_dict = grab_doc_from_mongo({'_id' : anime_object_id},
                                                         mongodb_database_name,
                                                         mongodb_anime_collection,
                                                         thread_info_enabled=thread_info_enabled)
                except Exception as e :
                    print(e)

            # write to disk
            with open(anime_data_path + anime_name_to_file_name_json(anime_name), 'w+') as file :
                file.write(dumps(anime_dict, indent=json_indent_len))
            
            # read the season file entry
            season_dict = get_season_entry(season_name,
                                           season_url,
                                           to_mongodb = to_mongodb,
                                           thread_info_enabled = thread_info_enabled,
                                           season_data_path = season_data_path)
            
            # update the season dictionary
            anime_entry = next(anime for anime in season_dict['seasonal_anime'] if anime['name'] == anime_name)
            anime_entry['datetime_filled'] = datetime.now().strftime(datetime_format)

            # tries to update document to mongodb
            if to_mongodb :
                try :
                    season_object_id, res = update_doc_in_mongo({'_id' : season_dict},
                                                         season_dict,
                                                         mongodb_database_name,
                                                         mongodb_season_collection,
                                                         thread_info_enabled=thread_info_enabled)
                    if res :
                        season_dict = grab_doc_from_mongo({'_id' : season_object_id},
                                                          mongodb_database_name,
                                                          mongodb_season_collection,
                                                          thread_info_enabled=thread_info_enabled)
                except Exception as e :
                    print(e)

            # write change to disk
            with open(season_data_path + season_name_to_file_name_json(season_name), 'w+') as file :
                file.write(dumps(season_dict, indent=json_indent_len))
    else :
        # read the entry and return it
        with season_entry_RW_locks[season_name] :
            with open(anime_data_path + anime_name_to_file_name_json, 'r') as file :
                anime_dict = load(file)

    # close connection variables
    close_session(None, None, response)

    # return the season_dict
    return anime_dict

def anime_name_to_file_name_json(anime_name : str) -> str : 
    """
    anime_name_to_file_name_json : This function is a helper function make
    getting a file name more human readable.

    Arguments:
        anime_name -- The name of the anime as a string

    Returns:
        file name that should corispond to the season
    """
    return anime_name.lower().replace(' ', '_').replace('.', '-') + ".json"

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

def get_anime_background_section(anime_dict : dict, soup : BeautifulSoup) -> None :
    """
    get_anime_background_section -- This function grabs the background field
    from the page content.

    Arguments:
        anime_dict -- The dictionary containing the anime entry
        soup -- The response content from the session
    """
    soup = soup.find("td", class_="pb24")
    for div in soup.find_all('div', class_=['border_top', 'pb16', 'floatRightHeader']) :
        div.decompose()
    soup.prettify()

    textblock = []
    for element in soup :
        textblock.append(element.text)

    txt = ' '.join(textblock).strip()
    txt = txt[txt.find("Background") + len("Background"):].strip()
    anime_dict['background'] = txt
    print(txt)

def get_anime_character_staff_section(anime_url : str) -> tuple[dict, dict] :
    """
    get_anime_character_staff_section -- This function will grab the character
    and staff information from each entry and record the results in seperate
    dictionary objects.

    TODO: needs to be finished

    Arguments:
        anime_url -- The url that is connected to the anime entry

    Returns:
        A tuple containing both the character and staff dictionaries.
    """
    response, retried, ret = init_session(anime_url + '/characters', get_anime_character_staff_section, [anime_url + '/characters'])[2:]
    if retried :
        return ret
    
    soup = BeautifulSoup(response.content, 'html.parser')
    character_ctx = soup.find_all('table', class_='js-anime-character-table')
    for ctx in character_ctx :
        character_name = ctx.find('h3', class_='h3_character_name').text.strip()
        print(character_name)
        for atx in ctx.find_all('tr', class_='js-anime-character-va-lang') :
            actor_link = atx.find('a').get('href')
            actor_name = atx.find('a').text
            print(f'{actor_name} - {actor_link}')
        print("=============================")

    return (None, None)
    