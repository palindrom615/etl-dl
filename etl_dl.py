#!/usr/bin/env python3
import argparse
import multiprocessing
import os
from functools import partial

from bs4 import BeautifulSoup
from dotenv import dotenv_values

from helpers.dl_week_material import dl_week_material, norm_filename
from helpers.login import login


def parse_args():
    config = dotenv_values(".env")
    MYSNU_ID = config.get("MYSNU_ID")
    MYSNU_PASSWORD = config.get("MYSNU_PASSWORD")

    parser = argparse.ArgumentParser()
    parser.add_argument("course_id", type=int)
    parser.add_argument("weeks", type=int, nargs="*")
    parser.add_argument("--my-snu-id", type=str, nargs="?", default=MYSNU_ID)
    parser.add_argument("--my-snu-pw", type=str, nargs="?", default=MYSNU_PASSWORD)
    return parser.parse_args()


def main(course_id: int, weeks: list[int], my_snu_id: str, my_snu_pw: str):
    session = login(my_snu_id, my_snu_pw)
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


if __name__ == "__main__":
    args = vars(parse_args())
    main(**args)
