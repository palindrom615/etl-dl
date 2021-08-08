#!/usr/bin/env python3
import argparse
import multiprocessing
import os
from functools import partial

from bs4 import BeautifulSoup

from helpers.dl_week_material import dl_week_material, norm_filename
from helpers.login import login

if __name__ == "__main__":
    session = login()

    parser = argparse.ArgumentParser()
    parser.add_argument("course_id", type=int)
    parser.add_argument("weeks", type=int, nargs="*")
    args = parser.parse_args()

    course_id = args.course_id
    weeks = args.weeks
    res = session.get(
        "http://etl.snu.ac.kr/course/view.php",
        params={"id": course_id},
    )
    soup = BeautifulSoup(res.content, features="html.parser")

    course_name = soup.select_one(".coursename").get_text()
    course_name = norm_filename(course_name)
    os.makedirs(f".site/{course_name}", exist_ok=True)
    os.chdir(f".site/{course_name}")

    if weeks:
        week_elements = [soup.select_one(f"li#section-{week}") for week in weeks]
    else:
        week_elements = soup.select("div.total_sections li.section")

    with multiprocessing.Pool() as pool:
        args = [str(week_element) for week_element in week_elements]
        pool.map(partial(dl_week_material, session), args)

    soup.decompose()
