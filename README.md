# MAL-scrubber

## Table of Contents

* [Description](https://github.com/Dr1p5ter/MAL-scrubber#Description)
* [Database Snapshots](https://github.com/Dr1p5ter/MAL-scrubber#Database_Snapshots)
* [Current Plans For Now](https://github.com/Dr1p5ter/MAL-scrubber#Current_Plans_For_Now)

## Description

> This application will incrimentally parse web packets through a website called myanimelist.net to get every series known up to the date the data was scrubbed. It will store the results in json format and encrypt the names of the anime records by the name using MD5.
> The intuition behind MD5 hash codes and why it is helpful is to provide a unique identifier that is within a 32 byte max field. Certain anime names consist of over 32 characters in length so this helps reduce the amount of storage. This can be managed my multiple
> threads but for now this is utilizing only 1 thread. I have to stress this, DO NOT flood servers without implimenting some sort of 'back off' protocol. If mine is utilized, there can be longer pauses. I don't take responsibility for anyone abusing servers with my
> code. Use responsibly.

## Database Snapshots

> I will upload data I personally grab off my computer. They are zipped using 7-ZIP and compressed roughly 8 times smaller than the original size. If wanting to do any processing over the data, access each record through the subfolder '\season_data' to allow for
> accurate and constant time I/O processes. Every record has a timestamp associated with the moment the file was downloaded. There are missing fields so make sure you take this into accound if you use the dataclass decorator in python.

## Current Plans For Now

> I want to make a file strictly for cleaning up each record. This is currently in a work in progress.
