# specified imports
from os import path, remove as rm, listdir, mkdir
from hashlib import md5
from anime_scrubber import anime_dir, season_dir, backtrack_list_file_name, CODE_I, CODE_C, CODE_E

def clean_data_dir() -> None :
    """
    clean_data_dir -- This function is a helper function to completely
    get rid of each data file once the MAL_season_link file needs to
    be generated.
    """
    # clean season_data directory
    if path.exists(season_dir) :
        for file in listdir(season_dir) :
            rm(season_dir + file)
    else :
        mkdir(season_dir)

    # clean anime_data directory
    if path.exists(anime_dir) :
        for file in listdir(anime_dir) :
            rm(anime_dir + file)
    else :
        mkdir(anime_dir)

def clean_backtrack_data() -> None :
    """
    clean_backtrack_data This function is a helper to clean out the
    season backtrack data.
    """
    # clean file if exists, otherwise make it
    if path.exists(backtrack_list_file_name) :
        rm(backtrack_list_file_name)
    open(backtrack_list_file_name, 'x')

def season_name_to_file_name(season_name : str) -> str : 
    """
    season_name_to_file_name : This function is a helper function make
    getting a file name more human readable.

    Arguments:
        season_name -- The name of the season as a string

    Returns:
        file name that should corispond to the season
    """
    return season_name.lower().replace(' ', '_') + ".json"

def anime_name_to_id(anime_name : str) -> str :
    """
    anime_name_to_id : This function is a helper function to make
    getting a file name that corisponds to an anime name

    Arguments:
        anime_name -- Thiss is name of the anime as a string

    Returns:
        MD5 hash of the string for unique identification
    """
    return md5(anime_name.encode("UTF-8")).hexdigest()

def resultant_dict(seasonal_retrieval_results : list) -> dict :
    """
    resultant_dict : This function is a helper function to tally
    up the completed codes within the JSON. It allows for the main
    program can submit this entry into the backtrack list so it won't
    be captured again if an error occurs with a file. This can happen.

    Arguments:
        seasonal_retrieval_results -- list of all completed codes within
        a season json file. These are recorded within the time of
        events occuring.

    Returns:
        dictionary containing values of each code
    """
    # init resultant
    res = {}
    res[CODE_I] = 0
    res[CODE_C] = 0
    res[CODE_E] = 0

    # go through each resultant once
    for code in seasonal_retrieval_results :
        res[code] += 1

    return res