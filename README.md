# eTL-dl

This tool helps you downloading course materials from eTL.

## Usage

You should make sure these programs are installed in your computer:

* [python3](https://www.python.org/downloads/)
* [ffmpeg](http://www.ffmpeg.org/download.html)

Follow these steps:
1. Run `python -m pip install -r requirements.txt` to install libraries.
1. Fill in `.env` file with your mySNU ID and password.
1. Run `python etl_dl.py <COURSE_ID>` (or `python etl_dl.py <COURSE_ID> <WEEK_NUMBER>` for confining downloading to specific weeks) and then course materials will be downloaded in `.site` directory.
    
    Course id can be found in URL of ETL course page.
