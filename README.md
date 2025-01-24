# Project Archived

This has been a fun experience but there is a few things I need to note about this repository:

1. This program is still runnable and works however, there is some optomization that needs to be covered
2. I will still provide detailed instructions on usage of scrubber.py below
3. Please check out my new version that I am making soon [here](...)

# MAL-Scrubber Project

This project was intended on being a web crawler that snags information on webpages hosted by [MyAnimeList](https://myanimelist.net/#) with the purpose of gathering data. This data can be shared online with everyone and used for their own gain or to use for their personal projects.

## Requirements

* Python 3.6+
    * BeautifulSoup
    * pymoongo
    * typing
    * requests

## Usage

There are two important things to consider when beginning the scrubber.py script. These will be highlighted below:

### MongoDB Instance Connection
    Within the util/mongodb.py file, there exists some important session variables to consider. The first being mongodb_database_name which has a default value "MAL-Scrubber" stored as a string. This variable primarily serves to connect the pymongo client to the MongoDB instance. When booting up MongoDB Atlas or the MongoDB Shell, this must be the name for the database in order to utilize the dynamic schema functionality of NoSQL databases. This value can be changed by default and will not alter the functionality of the app (so long as it can establish a connection to the host).

    The variable mongodb_host by default set to "mongodb://localhost:27017/" as a string, can be modified as well if the mongodb instance is not hosted using your local machine. This again only serves as backbone to the pymongo client.

    "A note about about the collections within your database, these should stay the same and shouldn't be modified. They are crucial aspects in the functionality and naming convention I have set up. If you do tinker with the collection names than I insist you do it at your own discretion."
    - Matt

### Runtime
    I use argparse to allow users upon runtime of scrubber.py to modify the use and functionality that is being provided. If you get confused on what each flag is doing then use the -h flag. Concurrent functionality can sometimes seem like race conditions come with the cons when in reality they should never happen. Debugging as a choice helps not only me but you figure out if there is a bug I can iron out at a later date.

## Archive Data Folder

There are 7Zip folders that hold compressed snapshots of my own personal runtime of the program. The format of such data has changed when I ran it last. I expect my attribute names to be human readable and therefore not needing a README going over each small detail. At a later time I will incorperate better and more complex data in the future in the next version mentioned in the [Project Archive](https://github.com/Dr1p5ter/MAL-scrubber#Project-Archived) section above. 

## Contact

Feel free to contact me regarding any questions you might have!

**Name:** *Matthew McLaren*  
**Business Email:** *mmclaren2021@outlook.com*