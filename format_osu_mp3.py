# Link to osu web api wiki: https://github.com/ppy/osu-api/wiki

import argparse
import os
import shutil
import eyed3
import logging
import zipfile
import json

from shutil import copyfile
from enum import Enum
from urllib import request, error as url_error
from eyed3 import id3

logging.getLogger("eyed3.mp3.headers").setLevel(logging.CRITICAL)

class KEYS(Enum):
    VERSION         = 0
    AUDIO_FILENAME  = 1
    MODE            = 2
    TITLE           = 3
    TITLE_UNICODE   = 4
    ARTIST          = 5
    ARTIST_UNICODE  = 6
    CREATOR         = 7
    TAGS            = 8
    BEATMAP_ID      = 9
    BEATMAP_SET_ID  = 10
    BG_FILENAME     = 11

GENRE_DICT = {
    0   :"any",
    1   :"unspecified",
    2   :"video game",
    3   :"anime",
    4   :"rock",
    5   :"pop",
    6   :"other",
    7   :"novelty",
    9   :"hip hop", # note that there's no 8
    10  :"electronic"
}

LANG_DICT = {
    0   :"any",
    1   :"other",
    2   :"english",
    3   :"japanese",
    4   :"chinese",
    5   :"instrumental",
    6   :"korean",
    7   :"french",
    8   :"german",
    9   :"swedish",
    10  :"spanish",
    11  :"italian"
}

def is_osz_zip(zip_name):
    return zip_name[-4:] == ".osz"

def read_osu_file(file_path):
    with open(file_path, mode='r', encoding="shift_jisx0213", errors="replace") as osuf:
        data_dict = {
            KEYS.VERSION:int(osuf.readline().split("osu file format v")[1]),
            KEYS.AUDIO_FILENAME: "",
            KEYS.MODE: "",
            KEYS.TITLE: "",
            KEYS.TITLE_UNICODE: "",
            KEYS.ARTIST: "",
            KEYS.ARTIST_UNICODE: "",
            KEYS.CREATOR: "",
            KEYS.TAGS: "",
            KEYS.BEATMAP_ID: "",
            KEYS.BEATMAP_SET_ID: "",
            KEYS.BG_FILENAME: ""
        }
        if data_dict[KEYS.VERSION] >= 3:
            key_pairs = get_keys_for_ver(data_dict[KEYS.VERSION])
            if not key_pairs:
                print("Failed to retrieve key pairs for version:\t%s" % data_dict[KEYS.VERSION])
                return {}
            keys_index = 0
            key_pair = key_pairs[keys_index]
            for line in osuf:
                if line.strip() == "[TimingPoints]":
                    break
                elif key_pair[1] in line:
                    data_dict[key_pair[0]] = line[len(key_pair[1]):].strip()
                    keys_index += 1
                    if keys_index < len(key_pairs):
                        key_pair = key_pairs[keys_index]
                elif "0,0," in line and (".jpg" in line or ".png" in line):
                    data_dict[KEYS.BG_FILENAME] = line.split("\"")[1]
            if keys_index < len(key_pairs):
                return {} # failed to read file
        return data_dict

def find_and_read_osu_file(file_path):
    target_file = r""
    target_data = {}
    if os.path.isdir(file_path):
        for file in os.listdir(file_path):
            if file[-4:] == ".osu":
                target_file = os.path.join(file_path, file)
                target_data = read_osu_file(target_file)
                if target_data[KEYS.MODE] == 0: # script prioritizes standard mode
                    return target_data, target_file
    if target_data:
        return target_data, target_file # no standard mode exists so return what has been found
    return {}, target_file # script failed

def get_keys_for_ver(ver):
    if ver <= 2:
        return [] # invalid version
    elif 3 <= ver <= 5:
        return [(KEYS.AUDIO_FILENAME, "AudioFilename: "), (KEYS.TITLE, "Title:"), (KEYS.ARTIST, "Artist:"),
                (KEYS.CREATOR, "Creator:")]
    elif 6 <= ver <= 9:
        return [(KEYS.AUDIO_FILENAME, "AudioFilename: "), (KEYS.MODE, "Mode: "), (KEYS.TITLE, "Title:"),
                (KEYS.ARTIST, "Artist:"), (KEYS.CREATOR, "Creator:"), (KEYS.TAGS, "Tags:")]
    else:  # ver 10, 11, 12, 13, 14, or above
        return [(KEYS.AUDIO_FILENAME, "AudioFilename: "), (KEYS.MODE, "Mode: "), (KEYS.TITLE, "Title:"),
                (KEYS.TITLE_UNICODE, "TitleUnicode:"), (KEYS.ARTIST, "Artist:"), (KEYS.ARTIST_UNICODE, "ArtistUnicode:"),
                (KEYS.CREATOR, "Creator:"), (KEYS.TAGS, "Tags:"), (KEYS.BEATMAP_ID, "BeatmapID:"),
                (KEYS.BEATMAP_SET_ID, "BeatmapSetID:")]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--songs_path", default="./", # parent directory is default
                        help="path to your osu songs folder (default is script's parent directory)")
    parser.add_argument("-k", "--key", default="",
                        help="your osu api key. adding this will provide extra metadata to your mp3 files "
                             "including genre and language")
    args = parser.parse_args()
    # Validate inputs
    songs_path = args.songs_path
    if not os.path.exists(songs_path):
        print("Provided path does not exist")
        exit(1)
    key = args.key
    if key:
        try:
            request.urlopen(r"https://osu.ppy.sh/api/get_beatmaps?k={}".format(key))
        except url_error.URLError:
            print("Could connect to osu api")
            exit(1)
    # Create temp path to store extracted folders
    temp_path = os.path.join( songs_path, "temp")
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)
    # Create folder to store formatted mp3's
    formatted_dest = os.path.join( songs_path, "formatted_mp3")
    if not os.path.exists(formatted_dest):
        os.mkdir(formatted_dest)
    # Main loop
    for directory in os.listdir(songs_path):
        # Find .osz zip file
        song_path = os.path.join(songs_path, directory)
        if not zipfile.is_zipfile(song_path) or not is_osz_zip(directory):
            continue # not a file of interest
        # Extract .osz zip file
        with open(song_path, 'rb') as zf:
            z = zipfile.ZipFile(zf)
            extract_to = os.path.join(temp_path, os.path.basename(song_path)[:-4])
            if not os.path.exists(extract_to):
                os.mkdir(extract_to)
            z.extractall(extract_to)
        # Find and read .osu file
        file_data, osu_file = find_and_read_osu_file(extract_to)
        if not osu_file:
            print("Failed to find .osu file in:\t%s" % song_path)
            continue
        if not file_data:
            print("Failed to read .osu file at:\t%s" % osu_file)
            continue
        # If .osu file version < 10 find set ID in zip file name
        if file_data[KEYS.VERSION] < 10:
            split = directory.split()
            if split[0].isdigit():
                file_data[KEYS.BEATMAP_SET_ID] = split[0]
        if not file_data[KEYS.BEATMAP_SET_ID]:
            print("Failed to find beatmap set ID for:\t%s" % song_path)
            continue
        # Find mp3, copy it, rename it, edit metadata
        mp3_file_path = os.path.join(extract_to, file_data[KEYS.AUDIO_FILENAME])
        copy_mp3_name = (file_data[KEYS.ARTIST] + " - " + file_data[KEYS.TITLE] + ".mp3")\
            .replace(':', "_").replace('\\','-').replace('*', '~')
        mp3_dest = os.path.join(formatted_dest, copy_mp3_name)
        copyfile(mp3_file_path, mp3_dest)
        # Load mp3, give it a tag if it doesn't already exists
        audioFile = eyed3.load(mp3_dest)
        audioFile.tag = eyed3.id3.Tag()
        audioFile.tag.file_info = eyed3.id3.FileInfo(mp3_dest)
        # Add genre and language if api key was given
        comment = ""
        if key:
            with request.urlopen(r"https://osu.ppy.sh/api/get_beatmaps?k={}&s={}"
                                                .format(key, file_data[KEYS.BEATMAP_SET_ID])) as response:
                data = json.loads(response.read())[0]
            audioFile.tag.genre = GENRE_DICT[int(data["genre_id"])]
            comment += "Language: " + LANG_DICT[int(data["language_id"])] + " "
        # Add front cover image
        if file_data[KEYS.BG_FILENAME]:
            bg_file_path = os.path.join(extract_to, file_data[KEYS.BG_FILENAME])
            imageData = open(bg_file_path, "rb").read()
            audioFile.tag.images.set(3, imageData, mime_type="")
        # Add other metadata and save
        audioFile.tag.artist = file_data[KEYS.ARTIST]
        audioFile.tag.title = file_data[KEYS.TITLE]
        audioFile.tag.comments.set(comment + "Tags: " + file_data[KEYS.TAGS])
        audioFile.tag.album = file_data[KEYS.CREATOR]
        audioFile.tag.save()
    # Delete temp directory
    shutil.rmtree(temp_path)

__all__ = ['argparse', 'os', 'shutil', 'eyed3', 'logging', 'zipfile',
           'json', 'copyfile', 'Enum', 'request', 'url_error', 'id3']