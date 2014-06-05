#!/usr/bin/python
"Extracts metadata from MP3 files into a mySQL database"

# read_mp3_metadata - Uses Mutagen library to extract ID3 tags and
# other metadata from MP3 music files.
#
#
# UNICODE COMPATIBILITY:
#
# This program still cannot save unicode file names.  This is due to
# Mutagen MP3 class not accepting unicode file names.
#
# Foreign language music may have unicode characters, which are
# lost if converted to ASCII.  Want to maintain original unicode
# characters, if possible.
#
# While writing this program, I encountered the following issues:
#
# 1. Mutagen MP3 and ID3 objects return unicode strings.
#   For example, see extractID3Frame().  Make sure not to convert
#   to ASCII with the str() function.
#
# 2. Must open connection to mySQLdb with unicode and utf8 support.
#   To do this:
#
#   db = MySQLdb.connect(host="YOUR_HOST_HERE",\
#                        user="YOUR_USER_HERE",\
#                        passwd="YOUR_PASSWD_HERE",\
#                        use_unicode=True,\
#                        charset="utf8")
#
# 3. Some file names are in unicode.  Use os.walk() to recursively
#   go through all subdirectories.  Must use unicode starting directory
#   in os.walk(), like this (Must have two backslashes
#   '\\' between directories.):
#
# startDir = u'C:\\Users\\Me\\Music\\iTunes\\Chuck Mangione'
# rootDir = u''
# dirs = u''
# for rootDir, dirs, files in os.walk(startDir):
#

import MySQLdb                  # mySQL library
from mutagen.mp3 import MP3   # Mutagen MP3 library
import os                       # Operating System library
import sys
import re                     # Regular expression library

# Create Metadata table in Songs database.  Define the  fields.
#
# Usage:
#
#   createDatabaseTable(cursor)
#
#       cursor - database cursor object
def createDatabaseTable(cursor):
    # create Music database, if it does not already exist
    cursor.execute("CREATE DATABASE IF NOT EXISTS MUSIC")
    cursor.execute("USE MUSIC")     # use Music database
    # delete Meta table if exists
    cursor.execute("DROP TABLE IF EXISTS META")

    # create Stats table, and define fields
    cursor.execute("CREATE TABLE Meta(title VARCHAR(100),\
                    artist VARCHAR(100),\
                    album VARCHAR(100),\
                    genre VARCHAR(50),\
                    date VARCHAR(20),\
                    length FLOAT,\
                    bitrate INT\
                    )")    # make Metadata table in Songs database


# Extract ID3 Frame data.  id3Frame='TIT2' for title, etc.
# 1. Use try / except statement to catch missing tags.
# 2. If tag value is blank (''), replace with 'N/A'
def extractID3Frame(song, songKey, id3Frame, mp3_file):
    missingString = 'N/A'
    
    try:
        # If id3Frame is 'TDRC' or 'TDAT' (to get the date), Mutagen
        # MP3 object returns a mutagen._id3specs.ID3TimeStamp object,
        # instead of a unicode string.  To get unicode string, must get
        # the text property of this object.
        if id3Frame == 'TDRC' or id3Frame == 'TDAT':
            song[songKey] = mp3_file[id3Frame].text[0].text
        else:
            song[songKey] = mp3_file[id3Frame].text[0]
            
        song[songKey] = escapeQuotes(song[songKey])
    except Exception:
        print(songKey + ' field not found.')
        song[songKey] = missingString
    else:
        if song[songKey] == '':
            song[songKey] = missingString


# Extract MP3 Metadata, such as bitrate, length of song, etc.
# 1. Use try / except statement to catch missing tags.
# 2. If tag value is blank (''), replace with 'N/A'
def extractMP3Info(song, songKey, mp3_file):
    # 'bitrate' and 'length' are numbers.
    # If these metadata are missing, replace with '0'.
    # 'N/A' will cause error in the numeric mySQL fields.
    missingString = '0'     
    
    try:
        if songKey == 'bitrate':            
            song[songKey] = mp3_file.info.bitrate
        elif songKey == 'length':
            song[songKey] = mp3_file.info.length
            
    except Exception:
        print(songKey + ' field not found.')
        song[songKey] = missingString
    else:
        if song[songKey] == '':
            song[songKey] = missingString

        
def extractMetadata(mp3_file, song):
    # Determine if ID3 version is 2.4 or greater
    bID3Ver24Plus = isID3Ver24(mp3_file)

    # Extract ID3 tags from file.
    extractID3Frame(song, 'title', 'TIT2', mp3_file)    # song title
    extractID3Frame(song, 'artist', 'TPE1', mp3_file)   # artist name
    extractID3Frame(song, 'album', 'TALB', mp3_file)    # album name
    extractID3Frame(song, 'genre', 'TCON', mp3_file)    # song genre
    
    if bID3Ver24Plus:                                   # song date (year)
        extractID3Frame(song, 'date', 'TDRC', mp3_file)
    else:
        extractID3Frame(song, 'date', 'TDAT', mp3_file)

    extractMP3Info(song, 'length', mp3_file)   # song length (secs)
    extractMP3Info(song, 'bitrate', mp3_file)  # song bitrate


# determine if ID3 version of file is 2.4 or greater.
# If so, return True.  Else return False.
def isID3Ver24(mp3_file):
    
    # Extract ID3 version
    if mp3_file.ID3.version[0] == 2 and mp3_file.ID3.version[1] >= 4:
        bVerGreaterThan24 = True    # ID3 version >= 2.4
    elif mp3_file.ID3.version[0] > 2:
        bVerGreaterThan24 = True    # ID3 version >= 2.4
    else:
        bVerGreaterThan24 = False   # ID3 version < 2.4

    return bVerGreaterThan24


def insertToDatabaseTable(cursor, db, song):
    # Insert data into Metadata table
    cmd = 'INSERT INTO Meta VALUES ' + \
        '(' + \
        '"' + song['title'] + '",' + \
        '"' + song['artist'] + '",' + \
        '"' + song['album'] + '",' + \
        '"' + song['genre'] + '",' + \
        '"' + song['date'] + '",' + \
        str(song['length']) + ',' + \
        str(song['bitrate']) + ')'
    print(cmd)
    cursor.execute(cmd)
    db.commit()         # commit change to database


# If a string has single or double quotes within it, it could
# cause problems when inserting into the database.
#
# So if str = 'internal "quote" here'
#
# You want to remove the internal quotes, such that
# str = 'internal quote here'
def removeInternalQuotes(metaString):
    singleOrDoubleQuote = '[\'\"]'  # Regular expression to search for ' or "
    replaceWith = ''                # Replace ' or " with ''

    # Set str equal to str without quotes.
    metaString = re.sub(singleOrDoubleQuote, replaceWith, metaString)

    return metaString

# Allow unicode strings to contain quotes by "escaping" them.
#
# s = u'There are 'quotes' here'
#
# The preceding unicode string will cause an error.  You must
# escape the single quotes like this:
#
# s = u'There are \'quotes\' here'
def escapeQuotes(metaString):
    singleQuote = '[\']'  # Regular expression to search for '
    singleQuoteEscaped = "\\'"   # escaped single quote
    doubleQuote = '[\"]'  # Regular expression to search for "
    doubleQuoteEscaped = '\\"'   # escaped double quote

    # Escape any single quotes.
    metaString = re.sub(singleQuote, singleQuoteEscaped, metaString)
    # Escape any double quotes.
    metaString = re.sub(doubleQuote, doubleQuoteEscaped, metaString)

    return metaString

# Get parameters to connect to mySQL database, then connect.
def connectMySQL():
    hostName = raw_input("Enter mySQL hostname: ")
    userName = raw_input("Enter mySQL username: ")
    password = raw_input("Enter mySQL password: ")
    
    print("mySQL hostName = %s, userName = %s, password = %s" % \
                  (hostName, userName, password))

    # Can you open the mySQL database with the given parameters?
    try:    
        # Open database connection
        db = MySQLdb.connect(host=hostName,\
                             user=userName,\
                             passwd=password,\
                             use_unicode=True,\
                             charset="utf8")
    except:
        print("Error: MySQLdb: failed to connect.  Exit program.")
        sys.exit()  # terminate program

    return db

# Get starting (top level) directory for MP3 library.
def getStartDirectory():
    startDir = raw_input("Enter top directory of MP3 library: ")

    # Convert startDir into Unicode
    startDir = unicode(startDir)
    print("startDir = %s" % startDir)

    # is startDir a valid directory?
    try:
        oldDir = os.getcwd()    # remember original directory
        os.chdir(startDir)
    except:
        print("Error: %s is not a valid directory.  Exit program." % startDir)
        sys.exit()  # terminate program

    os.chdir(oldDir)    # return to original directory
    return startDir


# Connect to mySQL database
db = connectMySQL()

# Get startDir (top level directory of MP3 library)
startDir = getStartDirectory()

# prepare a cursor object using cursor() method
cursor = db.cursor()
createDatabaseTable(cursor)

# Define dictionary data structure for a song
songDict = {'title': '', \
        'artist': '', \
        'album': '', \
        'genre': '', \
        'date': '', \
        'length': '', \
        'bitrate': ''}

# IMPORTANT: os.walk() must be given a unicode directory in order
# to return unicode file names and directories. Must have two backslashes
# '\\' between directories.
#startDir = u'C:\\Users\\Selwyn\\Music\\iTunes\\Podcasts\\JapanesePod101.com _ Learn Japanese (Aud'
#startDir = u'C:\\Users\\Selwyn\\Music\\iTunes'

# Create Unicode strings to use with os.walk().
# Need to handle Unicode characters in file and directory names.
rootDir = u''
dirs = u''
files = u''
for rootDir, dirs, files in os.walk(startDir):
    print('rootDir = ', rootDir, ' dirs = ', dirs, ' files = ', files)
    os.chdir(rootDir)   # change to root directory

    for f in files:
        if f.endswith('.mp3'):       # Found MP3 file
            print('MP3 file: ', f)
            audio = MP3(f)
            extractMetadata(audio, songDict)
            print(songDict)
            insertToDatabaseTable(cursor, db, songDict)

db.close()
