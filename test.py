import unittest
import os
from util.season import *
# from util.anime import *

season_data_test_path = '_test_season_data/'
anime_data_test_path = '_test_anime_data/'

def clear_season_data_test_subdirectory() :
    for file in os.listdir(season_data_test_path) :
        os.remove(season_data_test_path + file)

def clear_anime_data_test_subdirectory() :
    for file in os.listdir(anime_data_test_path) :
        os.remove(anime_data_test_path + file)

class TestSeasonMethods(unittest.TestCase) :
    def testA_init_season_subdir_clear(self) :
        self.assertTrue(path.exists(season_data_test_path))
        self.assertTrue(len(os.listdir(season_data_test_path)) < 1)

    def testB_make_season_list_to_csv(self) :
        season_entry_count = make_season_list_to_csv(skip_if_exists=False, 
                                                     thread_info_enabled=False, 
                                                     season_data_path=season_data_test_path)
        self.assertTrue(os.path.exists(season_data_test_path + season_file))
        self.assertTrue(os.stat(season_data_test_path + season_file).st_size > 0)
        self.assertTrue(season_entry_count > 0)
        self.assertTrue(len(os.listdir(season_data_test_path)) < 2)
        self.assertTrue(len(season_entry_RW_locks.keys()) == season_entry_count)
        
        clear_season_data_test_subdirectory()
        self.assertTrue(len(os.listdir(season_data_test_path)) == 0)
    
    def testC_season_name_to_file_name_json(self) :
        self.assertEqual(season_name_to_file_name_json("My Season"), "my_season.json")
        self.assertEqual(season_name_to_file_name_json("Season"), "season.json")

    # this test was hard coded (should not fail ever)
    def testD_get_season_entry_anime_present(self) :
        season_entry_count = make_season_list_to_csv(skip_if_exists=False, 
                                                     thread_info_enabled=False, 
                                                     season_data_path=season_data_test_path)
        season_entry_not_none = get_season_entry("Spring 2025",
                                                 "https://myanimelist.net/anime/season/2025/spring",
                                                 False, 
                                                 thread_info_enabled=False,
                                                 season_data_path=season_data_test_path)
        self.assertIsNotNone(season_entry_not_none != None)
        self.assertTrue(path.exists(season_data_test_path + season_name_to_file_name_json("Spring 2025")))
        self.assertTrue(os.stat(season_data_test_path + season_name_to_file_name_json("Spring 2025")).st_size > 0)
        self.assertTrue(len(season_entry_RW_locks.keys()) == season_entry_count)
        
        clear_season_data_test_subdirectory()
        self.assertTrue(len(os.listdir(season_data_test_path)) == 0)

    def testE_get_season_entry_no_anime_present(self) :
        season_entry_count = make_season_list_to_csv(skip_if_exists=False, 
                                                     thread_info_enabled=False, 
                                                     season_data_path=season_data_test_path)
        season_entry = get_season_entry("Spring 1918",
                                        "https://myanimelist.net/anime/season/1918/spring",
                                        False,
                                        thread_info_enabled=False,
                                        season_data_path=season_data_test_path)
        self.assertIsNone(season_entry)
        self.assertFalse(path.exists(season_data_test_path + season_name_to_file_name_json("Spring 1918")))
        with open(season_data_test_path + season_file, 'r') as file :
            lines = [(line.split(', ')[0].strip(), line.split(', ')[1].strip()) for line in file.readlines()]
            with self.assertRaises(ValueError):
                lines.index(("Spring 1918", "https://myanimelist.net/anime/season/1918/spring"))
        self.assertTrue(len(season_entry_RW_locks.keys()) == season_entry_count - 1)

        clear_season_data_test_subdirectory()
        self.assertTrue(len(os.listdir(season_data_test_path)) == 0)

# TODO: anime test files