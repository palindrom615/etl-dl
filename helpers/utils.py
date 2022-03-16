import asyncio
import re
import unicodedata
import multiprocessing

REQ_HEADERS = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36 Edg/88.0.705.81",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8,ja;q=0.7",
    "Origin": "https://etl.snu.ac.kr",
    "Content-Type": "application/x-www-form-urlencoded",
    "Sec-Fetch-Site": "same-site",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
    "Referer": "https://etl.snu.ac.kr/",
}
CONCURRENT_DOWNLOADS = multiprocessing.cpu_count()
semaphore = asyncio.Semaphore(CONCURRENT_DOWNLOADS)


def limit_concurrent(f):
    async def wrapper(*args, **kwargs):
        async with semaphore:
            return await f(*args, **kwargs)

    return wrapper


def valid_filepath(location: str, filename: str) -> str:
    filename = unicodedata.normalize("NFKC", filename)
    filename = re.sub(r"[^\w\s\-_\.,\(\)]", "_", filename)
    return f"{location}/{filename}"
