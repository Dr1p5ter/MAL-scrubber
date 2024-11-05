from util.init import *
from util.season import *
from util.anime import *
import concurrent.futures
from json import dump, load
from sys import stdout

# does nothing CRUD app
if __name__ == '__main__' :

    dicts = get_anime_character_staff_section("https://myanimelist.net/anime/55791/Oshi_no_Ko_2nd_Season")
    print(dicts[0])
    print(dicts[1])





























    # # initialize the season list
    # season_entry_count = make_season_list_to_csv()

    # # grab season information for every season
    # title_url_pairing = []
    # with open(season_dir + season_file, 'r') as file :
    #     [title_url_pairing.append((line.split(', ')[0].strip(),
    #                                line.split(', ')[1].strip())) 
    #      for line in file.readlines()
    #      if len(line.strip()) > 0]
        
    # # go through each season using threads
    # with concurrent.futures.ThreadPoolExecutor() as executor :
    #     futures = [executor.submit(get_season_entry, pair[0], pair[1]) for pair in title_url_pairing]

    #     for future in concurrent.futures.as_completed(futures) :
    #         pass

    