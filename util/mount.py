# imports

from requests import Session, Response
from requests.adapters import HTTPAdapter
from requests.exceptions import RetryError
from time import sleep
from threading import get_ident
from typing import Any, Callable
from urllib3.util import Retry

# static var

retry_time = 3 * 60                                                  # retry time in case of time out
retry_strategy = Retry(                                              # retry policy for each session
    total=8,                                                         #
    backoff_factor=15,                                               # DO NOT MODIFY
    backoff_max=60*4,                                                #
    backoff_jitter=5,                                                #
    status_forcelist=[405, 429, 500, 502, 503, 504],                 #
)                                                                    #

# functions

def init_session(url : str,
                 retry_func : Callable,
                 thread_info_enabled : bool,
                 args : list = [],
                 kwargs : dict = {}) -> tuple[Any, bool, Any] :
    """
    init_session -- This function begins an http session with a url that will
    be used to parse the contents of a GET request. This function will retry 
    functions and needs to pass the function arguments within a list.

    Arguments:
        url -- String referencing the url to visit
        retry_func -- The parent function calling this function
        thread_info_enabled -- When threads are implimented this will allow a
        print statement for debugging
    
    Keyword Arguments:
        args -- The parent function's arguments ( default : [] )
        kwargs -- The parent function's keyward arguments ( default : {} )

    Returns:
        A tuple containing the content property of the Response class
        corrisponding to the HTTP request, a boolean that dictates if the
        function had to be retried, and the resultant of the retried call
        to the function.
    """
    try :
        # give a heads up in the console that this has been called
        if thread_info_enabled :
            print(f'thread {get_ident():5} is running init_session')

        # create an adaptor holding the retry policy
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # generate a session with the adapter
        session = Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # sent a GET request and raise for status changes other than success (200)
        response = session.get(url)
        response.raise_for_status()

        # grab the content from the response
        content = response.content

        # close session
        session.close()

        # return tuple after close
        return (content, False, None)
    except RetryError as exception:
        # give a heads up in the console that this has been called
        if thread_info_enabled :
            print(f'thread {get_ident():5} ran into a RetryError ({exception})')
        else :
            print(f'ran into a RetryError ({exception})')
        
        # close session
        session.close()

        # restart the entire season if a response error occurs
        sleep(retry_time)
        return (None, True, retry_func(*args, **kwargs))
