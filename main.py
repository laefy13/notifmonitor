import re
import time
from scraper import Scraper
import argparse
import os


def getCached(log_file_path, scraper):
    with open(log_file_path, "r", encoding="iso-8859-15") as file:
        new_content = file.read()
    pattern = r"/[^/]+?/status/\d+"

    matches = re.findall(pattern, new_content)
    print(matches)
    urls = []
    for url in reversed(matches):
        saved = scraper.isSaved(url)
        if saved:
            print(url)
            break
        scraper.addToQueue(url)


def scrapeNew(line: str, bmob_path: str, scraper):
    pattern = r"/[^/]+?/status/\d+"
    matches = re.findall(pattern, line)
    if not matches:
        return
    try:
        print("goint to scrapethis:", matches)
        scraper.addToQueue(matches[0])
    except Exception as e:
        print(f"scrapenew error: {e}")


def follow(thefile):
    thefile.seek(0, 2)
    try:
        while True:
            line = thefile.readline()
            if not line:
                time.sleep(1)
                continue
            yield line
    except Exception as e:
        raise e


def isNotNegative(num):
    inum = int(num)
    if inum < 0:
        raise argparse.ArgumentTypeError(f"{num} is less than 0")
    return inum


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
        default=r"C:\Users\fy\AppData\Local\Google\Chrome\User Data\Default\Platform Notifications\000004.log",
        type=str,
        help="path of the log file",
    )
    parser.add_argument(
        "--workers", type=int, default=3, help="number of workers/chrome windows"
    )
    parser.add_argument(
        "--max-retries",
        type=isNotNegative,
        default=0,
        help="number of retries before giving up",
    )

    args = parser.parse_args()

    log_file_path = args.path
    bmob_path = args.bmob_path
    workers = args.workers

    if not os.path.isfile(log_file_path):
        raise Exception("log file does not exist")

    logfile = open(
        log_file_path,
        "r",
        encoding="iso-8859-15",
    )

    scraper = Scraper(
        workers=workers, max_retries=args.max_retries, bmob_path=bmob_path
    )
    getCached(log_file_path, scraper)
    print("saved latest posts")

    try:
        loglines = follow(logfile)
        for line in loglines:
            scrapeNew(line, bmob_path, scraper)
    except KeyboardInterrupt:
        print("Script interrupted. Exiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "scraper" in locals():
            scraper.shutdown()
        if "logfile" in locals():
            logfile.close()
        print("Exiting...")
