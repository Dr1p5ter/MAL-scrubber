# MAL-scrubber

## Table of Contents

<!-- * [Installation](https://github.com/Dr1p5ter/MAL-scrubber#Installation) -->
* [Description](https://github.com/Dr1p5ter/MAL-scrubber#Description)
* [Testing](https://github.com/Dr1p5ter/MAL-scrubber#Testing)
* [MongoDB](https://github.com/Dr1p5ter/MAL-scrubber#MongoDB)
* [Database Snapshots](https://github.com/Dr1p5ter/MAL-scrubber#Database_Snapshots)
* [Current Plans For Now](https://github.com/Dr1p5ter/MAL-scrubber#Current_Plans_For_Now)
* [Contact](https://github.com/Dr1p5ter/MAL-scrubber#Contact)

## Description

> This project is dedicated to my personal growth with MongoDB and Flask. I want to emphasize I am not finished with all the parts but I am almost finished with the application portion. Most of the heavy lifting will be done through local instances that incorperating a naive approach to cacheing. Database retrieval will be set to default midst runtime with Flask. This portion of the project has not been implemented yet.

> The subdirectory '/util' contains most if not all of the helper functions that Flask will be using on runtime. app.py will be dedicated for Flask and all other html,css,js files will have their own subdirectories in the future.

> The subdirectory '/anime_data' and '/season_data' will hold cached data and will be used frequently during runtime. DO NOT delete the files or the subdirectories when running. Deletions should be made through a restart of application or from timestamp of data exceeding the 2 week threshold. Once exceeded the subdirectories are automatically deleted on start up.

#### Disclaimer
> I will change this at some point consult README.md for changes.

## Testing

> I have begun to extensively test with unittest for python 3.12 and can be done with any version past 3.6.* with the modules I have installed. I will make a requirement.txt later. Stay tuned.

### MongoDB

> Testing database implementation needs to be throughly investigated further. Stay tuned.

## Database Snapshots

> I have uploaded an archeived version of data grabbed prior to object retrieval changes. These can be accessed through 7Zip. They are compressed to about an 8th the size. This data is free and available to the public but keep in mind that the data is not complete and is dirty.

> Please consult '/archeive_data' for archeived snapshots.

## Current Plans For Now

> While I have a bunch of work I want to do with this project, nothing is more important right now than finishing the helper functions and beginning to implement Flask as well as a GUI app for users. I might make another repository dedicated to making a login system that works to access the data from both current and previous database snapshots.

## Contact

I am always eager to learn. If you think I can make something better feel free to contact me anytime!!

email: mmclaren2021@outlook.com