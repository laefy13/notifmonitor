import re
import time
from scraper import Scraper
import argparse


def using_sets(a, b):
    d = {j: i for i, j in enumerate(a)}
    return sorted(list((set(a) - set(b))), key=lambda x: d[x])


def getCached(log_file_path, scraper):
    with open(log_file_path, "r", encoding="iso-8859-15") as file:
        new_content = file.read()
    pattern = r"/[^/]+?/status/\d+"

    matches = re.findall(pattern, new_content)

    with open("saved.txt", "r", encoding="utf-8") as file:
        saved = file.readlines()
    lines = [line.strip() for line in saved]

    new_urls = using_sets(matches, lines)

    scraper.startScraping(new_urls)

    matches_str = "\n".join(matches)

    with open("saved.txt", "w", encoding="utf-8") as file:
        file.write(matches_str)


def scrapeNew(line: str, bmob_path: str, scraper):
    pattern = r"/[^/]+?/status/\d+"
    matches = re.findall(pattern, line)
    if not matches:
        return
    print(matches)
    scraper.addToQueue(matches[0])


def follow(thefile):
    thefile.seek(0, 2)
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(1)
            continue
        yield line


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bmob-path",
        type=str,
        default=r"D:\DESKTOP\browsermob-proxy-2.1.4\bin\browsermob-proxy",
        help="same path as the browsermob.py",
    )
    parser.add_argument(
        "--path",
        default=r"C:\Users\fy\AppData\Local\Google\Chrome\User Data\Default\Platform Notifications\000003.log",
        type=str,
        help="path of the log file",
    )
    parser.add_argument(
        "--workers", type=int, default=5, help="number of workers/chrome windows"
    )
    args = parser.parse_args()

    log_file_path = args.path
    bmob_path = args.bmob_path
    workers = args.workers

    logfile = open(
        log_file_path,
        "r",
        encoding="iso-8859-15",
    )
    loglines = follow(logfile)

    scraper = Scraper(workers=workers, bmob_path=bmob_path)
    getCached(log_file_path, scraper)
    for line in loglines:
        scrapeNew(line, bmob_path, scraper)
