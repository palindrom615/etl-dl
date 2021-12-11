# ETL-dl

This tool helps you downloading course materials from ETL.

## Usage

First you should make sure these programs to be installed in your computer:

* [python3](https://www.python.org/downloads/)
* [ffmpeg](http://www.ffmpeg.org/download.html)

Run `python -m pip install -r requirements.txt` to install libraries and fill in `.env` file with your my snu ID and password.

Run `python etl_dl.py <COURSE_ID>` or `python etl_dl.py <COURSE_ID> <WEEK_NUMBER`>...` and then course materials will be downloaded in `.site` directory.

Course id can be found in URL of ETL course page.
