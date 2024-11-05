# imports

from threading import Lock

# static var

anime_dir = "anime_data/"                                            # anime data directory path relative to util folder
datetime_format = "%m/%d/%Y %H:%M:%S"                                # format for the datetime variable
json_indent_len = 4                                                  # readable indent size
season_dir = "season_data/"                                          # seasonal data directory path relative to util folder
season_entry_RW_locks = {}                                           # all locks pertaining to each season
season_file_RW_lock = Lock()                                         # lock so threads can't cause a race condition