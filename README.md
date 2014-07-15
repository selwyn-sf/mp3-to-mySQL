mp3-to-mySQL
============

Extract metadata from your MP3 library into a mySQL database.  Written in Python.

The metadata fields extracted by this application are:

- Title - First 30 characters of song title.
- Artist - First 30 characters of song artist.
- Album - First 30 characters of album name.
- Genre - Rock, classical, etc.
- Date - Date of recording.

### Required Packages
- Python 2.7
- mutagen 1.22+ (Python MP3 library)
- mySQL


### Usage
Run mp3-to-mySQL either from the command prompt or from IDE.  You will prompted for the root directory where all your MP3 files reside.

mp3-to-mySQL will:

1. Recursively walk through all the subdirectories in your root directory.

2. In each subdirectory, it will find all MP3 files.

3. In each MP3 file, it will extract the metadata fields listed above, and put them into the mySQL database schema defined in this program.

After the program completes, there will be a **music** database in mySQL.  Within the **music** database, there will be a **meta** table.  The metadata for your entire MP3 library resides in this table.
