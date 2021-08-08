import requests
from bs4 import BeautifulSoup
from dotenv import dotenv_values

common_headers = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Referer": "http://etl.snu.ac.kr/course/view.php?id=197381",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7",
    "Origin": "https://etl.snu.ac.kr",
    "Content-Type": "application/x-www-form-urlencoded",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Referer": "https://etl.snu.ac.kr/",
}


def login() -> requests.Session:
    config = dotenv_values(".env")
    session = requests.Session()

    session.get("http://etl.snu.ac.kr/", headers=common_headers)
    res = session.post(
        "https://sso.snu.ac.kr/safeidentity/modules/auth_idpwd",
        headers=common_headers,
        data={
            "si_id": config.get("MYSNU_ID"),
            "si_pwd": config.get("MYSNU_PASSWORD"),
            "si_redirect_address": "https://sso.snu.ac.kr/snu/ssologin_proc.jsp?si_redirect_address=http://etl.snu.ac.kr/",
        },
        allow_redirects=False,
    )
    if res.headers.get("Location") is not None and "error" in res.headers.get(
        "Location"
    ):
        raise ValueError("Login Failed!")
    body = BeautifulSoup(res.content, "html.parser")
    data = {}
    for input in body.select("input"):
        data[input["name"]] = input["value"]
    session.post(
        "https://sso.snu.ac.kr/nls3/fcs",
        headers=common_headers,
        data=data,
    )
    return session
