# imports

from pymongo import MongoClient
from pymongo.synchronous.cursor import Cursor
from threading import Lock, get_ident
from typing import Any

# global var

anime_counter = 0
season_counter = 0

# static var

anime_counter_lock = Lock()                                          # lock used for the global anime counter
mongodb_anime_collection = 'animes'                                  # the anime collection within mongodb database
mongodb_database_name = "MAL-Scrubber"                               # the database associated with this project
mongodb_host = 'mongodb://localhost:27017/'                          # hostname of mongodb instance
mongodb_season_collection = 'seasons'                                # the season collection within mongodb database
season_counter_lock = Lock()                                         # lock used for the global season counter

# functions

def insert_doc_into_mongo(document : Any,
                          database : str,
                          collection : str,
                          thread_info_enabled : bool) -> bool :
    """
    insert_doc_into_mongo -- Insert a document object into mongodb.

    Arguments:
        document -- An acceptable form of data to be submitted to mongodb
        database -- The name of the database within mongodb
        collection -- The collection inside of the database
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging

    Raises:
        Exception: Connection/Issue pertaining to MongoDB

    Returns:
        Status as a boolean;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled is True :
        print(f'thread {get_ident():5} is running insert_doc_into_mongo')

    # make a connection to mongodb
    try:
        client = MongoClient(mongodb_host)
        client.admin.command("ping")

        # go to collection
        col = client[database][collection]

        # insert the object into the collection
        res = col.insert_one(document)

        # close the connection to mongodb
        client.close()

        return res.acknowledged
    except Exception as e:
        raise e

def grab_doc_from_mongo(query_criteria : dict,
                        database : str,
                        collection : str,
                        thread_info_enabled : bool) -> dict :
    """
    grab_doc_from_mongo -- Fetch a document from mongodb where each grab
    returns exactly one document.

    Arguments:
        query_criteria -- The criteria for the query to search on
        database -- The name of the database within mongodb
        collection -- The collection inside of the database
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging

    Raises:
        Exception: Connection/Issue pertaining to MongoDB

    Returns:
        The document is returned as a dictionary object;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running grab_doc_from_mongo')

    # make a connection to mongodb
    try:
        client = MongoClient(mongodb_host)
        client.admin.command("ping")

        # go to collection
        col = client[database][collection]

        # grab the document from mongodb
        document = col.find_one(query_criteria)

        # close the connection to mongodb
        client.close()

        return document
    except Exception as e:
        raise e

def update_doc_in_mongo(query_criteria : dict,
                        new_document : dict,
                        database : str,
                        collection : str,
                        thread_info_enabled : bool) -> bool :
    """
    update_doc_in_mongo -- update a document from mongodb.

    Arguments:
        query_criteria -- The criteria for the query to search on
        new_document -- The new document with changes
        database -- The name of the database within mongodb
        collection -- The collection inside of the database
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging

    Raises:
        Exception: Connection/Issue pertaining to MongoDB

    Returns:
        Status as a boolean;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running update_doc_in_mongo')

    # make a connection to mongodb
    try:
        client = MongoClient(mongodb_host)
        client.admin.command("ping")

        # go to collection
        col = client[database][collection]

        # replace old document
        res = col.replace_one(query_criteria, new_document)

        # close the connection to mongodb
        client.close()

        return res.acknowledged
    except Exception as e:
        raise e

def generate_cursor(database : str,
                           collection : str,
                           thread_info_enabled : bool,
                           query : dict = {}) -> Cursor :
    """
    generate_cursor : This functin will generate a cursor object for traversing
    a collection within the database. The query by default is set to empty to
    inclusively go through each document. This can be changed. There is no need
    to close the cursor explicitely since pymongo by default will close the
    cursor once there is no longer any more entries in the queue.

    Arguments:
        database -- The name of the database within mongodb
        collection -- The collection inside of the database
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging

    Keyword Arguments:
        query -- ruleset for the find operation used for making the cursor
        (default: {})

    Raises:
        Exception: Connection/Issue pertaining to MongoDB

    Returns:
        Cursor that holds entries being retrieved.
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled is True :
        print(f'thread {get_ident():5} is running generate_cursor')

    # make a connection to mongodb
    try:
        client = MongoClient(mongodb_host)
        client.admin.command("ping")

        # go to collection
        col = client[database][collection]

        # generate cursor
        cursor : Cursor = col.find(query)

        return cursor
    except Exception as e:
        raise e

def drop_docs_in_collection(collection : str) -> None :
    """
    drop_docs_in_collections -- This function is an initialization function in
    charge of cleaning the database to ensure insertions upon scrubbing doesn't
    insert documents with same key

    Arguments:
        collection -- the name of the collection to clean
    
    Raises:
        Exception: Connection/Issue pertaining to MongoDB
    """
    # make a connection to mongodb
    try :
        client = MongoClient(mongodb_host)
        client.admin.command("ping")

        # go to each collection and clean the documents in the database
        count_deleted = client[mongodb_database_name][collection].delete_many({})
        print(f'docs deleted in {collection} collection : {count_deleted}')

        # close the connection
        client.close()
    except Exception as e:
        print("Critical Error : connection couldn't clean database")
        exit(-5)

def get_anime_id() -> int :
    """
    get_anime_id -- This function will grab an anime id number used for
    mongodb.

    Returns:
        anime id as an integer
    """
    with anime_counter_lock :
        global anime_counter
        anime_counter += 1
        return anime_counter
    
def get_season_id() -> int :
    """
    get_season_id -- This function will grab a season id number used for
    mongodb.

    Returns:
        season id as an integer
    """
    with season_counter_lock :
        global season_counter
        season_counter += 1
        return season_counter
