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
                          thread_info_enabled : bool = False) -> tuple[Any, bool] :
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
        A tuple consisting of the object id of the document and the operations
        resulant status as a boolean;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running insert_doc_into_mongo')

    # make a connection to mongodb
    try:
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command("ping")

        # go to collection
        col = client[database][collection]

        # insert the object into the collection
        res = col.insert_one(document)

        # close the connection to mongodb
        client.close()

        return (res.inserted_id(), res.acknowledged())
    except Exception as e:
        raise e

def grab_doc_from_mongo(query_criteria : dict,
                        database : str,
                        collection : str,
                        thread_info_enabled : bool = False) -> dict :
    """
    grab_doc_from_mongo -- Fetch a document from mongodb where each grab
    returns exactly one document.

    Arguments:
        query_criteria -- The criteria for the query to search on
        database -- The name of the database within mongodb
        collection -- The collection inside of the database

    Keyword Arguments:
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging ( default: False )

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
        client = MongoClient("mongodb://localhost:27017/")
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
                        values : dict,
                        database : str,
                        collection : str,
                        thread_info_enabled : bool = False) -> tuple[Any, bool] :
    """
    update_doc_in_mongo -- update a document from mongodb.

    Arguments:
        query_criteria -- The criteria for the query to search on
        values -- The new value to change/modofy
        database -- The name of the database within mongodb
        collection -- The collection inside of the database

    Keyword Arguments:
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging ( default: False )

    Raises:
        Exception: Connection/Issue pertaining to MongoDB

    Returns:
        A tuple consisting of the object id of the document and the operations
        resulant status as a boolean;
    """
    # give a heads up in the console that this has been called
    if thread_info_enabled :
        print(f'thread {get_ident():5} is running update_doc_in_mongo')

    # make a connection to mongodb
    try:
        client = MongoClient("mongodb://localhost:27017/")
        client.admin.command("ping")

        # go to collection
        col = client[database][collection]

        # update the document from mongodb
        operation = {'$set' : values}
        res = col.update_one(query_criteria, operation)

        # close the connection to mongodb
        client.close()

        return (res.upserted_id(), res.acknowledged())
    except Exception as e:
        raise e
    