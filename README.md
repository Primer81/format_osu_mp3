# Purpose

The purpose of this Python script is to convert beatmap files downloaded from the osu! website (the zip files with the extension .osz) into mp3's of the corresponding song. These mp3's will have appropriate metadata including title, artist, tags, and a cover. The cover will be equal to whatever background the beatmap has ingame. If the set of beatmaps has multiple backgrounds, a random one will be chosen. In addition, if provided an osu! API key (obtained here: https://osu.ppy.sh/p/api), the script shall add genre and language as well (an internet connection is required). Because mp3's do not provide a language or tags field in their metadata, both language and tags are added to the comment field instead. The script also assumes that all of the songs you are converting are singles. As such, the beatmap set ID is inserted into the mp3's album field. This is to prevent dumb music players from not displaying your mp3's cover properly (some music players will only show one image for all mp3's of the same album. So if the album field were left empty, all of your mp3's would appear to have the same cover).

# Getting Started

1) You need to install Python 3.6.4 or higher from here: https://www.python.org/downloads/. When you are installing, make sure you check that box that asks you if you want to add Python to your path environment variable. It will make everything much easier.

2) Open the command prompt and type:

`
pip install eyed3
`

This will install the python library that is used in this script to modify the metadata of mp3's. If you get an error that "pip" is not recognized as a valid command then you probably haven't installed Python properly.

# How to use

Note: Make sure you've done everything in the "Getting Started" section before trying to use this script.

In order to use this script, all you need to do is download some beatmaps using your favorite method (I suggest http://osusearch.com). Once you've done that, you can just copy the script into the same directory/folder you downloaded your beatmaps into and double click it. A command prompt window should open (if it does not, make sure you're opening the script with python and not something else). eyed3 may print some errors to the command prompt window about non-standard genres and invalid timestamps. You can ignore those. Once the command prompt closes, the script will have finished and copied all of your converted mp3's into a folder called "formatted_mp3".
