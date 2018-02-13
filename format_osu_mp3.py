# Link to osu web api wiki: https://github.com/ppy/osu-api/wiki

import argparse
import os
import eyed3.id3
import logging
import zipfile

from shutil import copyfile
from enum import Enum

logging.getLogger("eyed3.mp3.headers").setLevel(logging.CRITICAL)

class Keys(Enum):
    VERSION         = 1
    AUDIO_FILENAME  = 2
    TITLE           = 3
    TITLE_UNICODE   = 4
    ARTIST          = 5
    ARTIST_UNICODE  = 6
    CREATOR         = 7
    TAGS            = 8
    BEATMAP_ID      = 9
    BEATMAP_SET_ID  = 10
    BG_FILENAME     = 11

def is_osz_zip(zip_name):
    return zip_name[:-4] == ".osz"

def find_osu_file(file_path):
    if os.path.isdir(file_path):
        for file in os.listdir(file_path):
            if file[-4:] == ".osu":
                return os.path.join(file_path, file)
    return "" # failed to find file

def read_osu_file(file_path):
    with open(file_path, mode='r', encoding="shift_jisx0213", errors="replace") as osuf:
        data = {
            Keys.VERSION:int(osuf.readline().split("osu file format v")[1]),
            Keys.AUDIO_FILENAME:"",
            Keys.TITLE:"",
            Keys.TITLE_UNICODE:"",
            Keys.ARTIST: "",
            Keys.ARTIST_UNICODE: "",
            Keys.CREATOR: "",
            Keys.TAGS: "",
            Keys.BEATMAP_ID: "",
            Keys.BEATMAP_SET_ID: "",
            Keys.BG_FILENAME:""
        }
        if data[Keys.VERSION] >= 3:
            key_pairs = get_keys_for_ver(data[Keys.VERSION])
            if not key_pairs:
                print("Failed to retrieve key pairs for version:\t%s" % data[Keys.VERSION])
                return {}
            keys_index = 0
            key_pair = key_pairs[keys_index]
            for line in osuf:
                if line.strip() == "[TimingPoints]":
                    break
                elif key_pair[1] in line:
                    data[key_pair[0]] = line[len(key_pair[1]):].strip()
                    keys_index += 1
                    if keys_index < len(key_pairs):
                        key_pair = key_pairs[keys_index]
                elif "0,0," in line and (".jpg" in line or ".png" in line):
                    data[Keys.BG_FILENAME] = line.split("\"")[1]
            if keys_index < len(key_pairs):
                return {} # failed to read file
        return data

def get_keys_for_ver(ver):
    if ver <= 2:
        return [] # invalid version
    elif 3 <= ver <= 5:
        return [(Keys.AUDIO_FILENAME,"AudioFilename:"), (Keys.TITLE,"Title:"), (Keys.ARTIST,"Artist:"),
                (Keys.CREATOR,"Creator:")]
    elif 6 <= ver <= 9:
        return [(Keys.AUDIO_FILENAME,"AudioFilename:"), (Keys.TITLE,"Title:"), (Keys.ARTIST,"Artist:"),
                (Keys.CREATOR,"Creator:"), (Keys.TAGS,"Tags:")]
    else:  # ver 10, 11, 12, 13, 14, or above
        return [(Keys.AUDIO_FILENAME,"AudioFilename:"), (Keys.TITLE,"Title:"), (Keys.TITLE_UNICODE,"TitleUnicode:"),
                (Keys.ARTIST,"Artist:"), (Keys.ARTIST_UNICODE,"ArtistUnicode:"), (Keys.CREATOR,"Creator:"),
                (Keys.TAGS,"Tags:"), (Keys.BEATMAP_ID,"BeatmapID:"), (Keys.BEATMAP_SET_ID,"BeatmapSetID:")]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--songs_path", help="path to your osu songs folder")
    parser.add_argument("-k", "--key", help="your osu api key")
    args = parser.parse_args()

    songs_path = args.songs_path
    if not songs_path:
        songs_path = os.path.dirname(__file__)
    elif not os.path.exists(songs_path):
        print("Provided path does not exist")
        exit(1)

    temp_path = os.path.join(os.path.dirname(__file__) + r"\temp")
    if not os.path.exists(temp_path):
        os.mkdir(temp_path)

    formatted_dest = os.path.join(os.path.dirname(__file__), r"\formatted_mp3")
    if not os.path.exists(formatted_dest):
        os.mkdir(formatted_dest)

    for directory in os.listdir(songs_path):
        # Find the beatmap set ID
        song_path = os.path.join(songs_path, directory)
        if not os.path.exists(song_path):
            print("Failed to find path to the following directory:\t%s" % directory)
            continue
        if not zipfile.is_zipfile(song_path) or not is_osz_zip(directory):
            continue # not a file of interest
        with open(song_path, 'rb') as zf:
            z = zipfile.ZipFile(zf)
            extract_to = os.path.join(temp_path, z.filename)
            z.extractall(extract_to)
        osu_file = find_osu_file(extract_to)
        if not osu_file:
            print("Failed to find .osu file in:\t%s" % song_path)
            continue
        file_data = read_osu_file(osu_file)
        if not file_data:
            print("Failed to read .osu file at:\t%s" % osu_file)
            continue
        split = directory.split()
        if split[0].isdigit():
            file_data[Keys.BEATMAP_SET_ID] = split[0]
        if not file_data[Keys.BEATMAP_SET_ID]:
            print("Failed to find beatmap set ID for:\t%s" % song_path)
            continue
        # Find mp3, copy it, rename it, edit metadata
        mp3_file_path = os.path.join(song_path, file_data[Keys.AUDIO_FILENAME])
        if not os.path.exists(formatted_dest):
            os.makedirs(formatted_dest)
        mp3_dest = os.path.join(formatted_dest, file_data[Keys.ARTIST] + " - " + file_data[Keys.TITLE] + ".mp3")
        copyfile(mp3_file_path, mp3_dest)
        # Load mp3, give it a tag if it doesn't already exists
        audioFile = eyed3.load(mp3_dest)
        if audioFile.tag is None:
            audioFile.tag = eyed3.id3.Tag()
            audioFile.tag.file_info = eyed3.id3.FileInfo(mp3_dest)
        # Add front cover image
        if file_data[Keys.BG_FILENAME]:
            bg_file_path = os.path.join(song_path, file_data[Keys.BG_FILENAME])
            imageData = open(bg_file_path, "rb").read()
            audioFile.tag.images.set(3, imageData, mime_type="")
        # Add other metadata and save
        audioFile.tag.artist = file_data[Keys.ARTIST]
        audioFile.tag.title = file_data[Keys.TITLE]
        audioFile.tag.save()
