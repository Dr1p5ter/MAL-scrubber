# imports

from pymongo import MongoClient
from threading import get_ident
from typing import Any

# static var

mongodb_database_name = "MAL-Scrubber"                               # the database associated with this project
mongodb_season_collection = 'seasons'                                # the season collection within mongodb database
mongodb_anime_collection = 'animes'                                  # the anime collection within mongodb database

# functions

def insert_doc_into_mongo(document : Any,
                          database : str,
                          collection : str,
                          thread_info_enabled : bool = False) -> bool :
    """
    insert_doc_into_mongo -- Insert a document object into mongodb.

    Arguments:
        document -- An acceptable form of data to be submitted to mongodb
        database -- The name of the database within mongodb
        collection -- The collection inside of the database

    Keyword Arguments:
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging ( default: False )

    Raises:
        Exception: Connection/Issue pertaining to MongoDB

    Returns:
        A confirmation of the result being written to mongodb; False means
        error in submission;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running insert_season_doc_into_mongo')

    # make a connection to mongodb
    try:
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command("ping")

        # go to collection
        season_collection = client[database][collection]

        # insert the object into the collection
        res = season_collection.insert_one(document)

        # close the connection to mongodb
        client.close()

        return res.acknowledged()
    except Exception as e:
        raise e
