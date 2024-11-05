# imports

from requests import Session, Response
from requests.adapters import HTTPAdapter
from requests.exceptions import RetryError
from time import sleep
from typing import Any, Callable
from urllib3.util import Retry

# static var

retry_time = 3 * 60                                                  # retry time in case of time out
retry_strategy = Retry(                                              # retry policy for each session
    total=3,                                                         #
    backoff_factor=5,                                                # DO NOT MODIFY
    status_forcelist=[405, 429, 500, 502, 503, 504],                 #
)                                                                    #

# functions

def init_session(url : str,
                 retry_func : Callable,
                 args : list = [],
                 kwargs : dict = {}) -> tuple[HTTPAdapter, Session, Response, bool, Any] :
    """
    init_session -- This function begins an http session with a url that will
    be used to parse the contents of a GET request. This function will retry 
    functions and needs to pass the function arguments within a list.

    Arguments:
        url -- String referencing the url to visit
        retry_func -- The parent function calling this function
        args -- The parent function's arguments ( default : [] )
        kwargs -- The parent function's keyward arguments ( default : {} )

    Returns:
        A tuple containing the http adapter, the http session, and the GET
        request from the session in that order;
    """
    try :
        # create an adaptor holding the retry policy
        adapter = HTTPAdapter(max_retries=retry_strategy)

        # generate a session with the adapter
        session = Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        # sent a GET request and raise for status changes other than success (200)
        response = session.get(url)
        response.raise_for_status()
        return (adapter, session, response, False, None)
    except RetryError as exception:
        # restart the entire season if a response error occurs
        print(f'{exception}')
        print(f'Error occured when session was attempting for packet retrieval, wait then retry aftr {retry_time / 60} minutes')
        sleep(retry_time)
        return (None, None, None, True, retry_func(*args, **kwargs))
