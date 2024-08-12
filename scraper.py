import json
import os
import random
from selenium import webdriver
from selenium_stealth import stealth

from browsermobproxy import Server
import time
import subprocess

from selenium.webdriver.common.by import By

import requests
import uuid
from queue import Queue
from concurrent.futures import ThreadPoolExecutor

from selenium.webdriver.common.keys import Keys
from PIL import Image
from io import BytesIO


class Scraper:
    def __init__(
        self,
        workers,
        bmob_path=r"C:\Users\fy\Desktop\browsermob-proxy-2.1.4\bin\browsermob-proxy",
    ):
        self.browsermob_proxy_path = bmob_path
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]

        self.vendors = [
            "Google Inc.",
            "Mozilla Foundation",
            "Microsoft Corporation",
        ]
        self.platforms = [
            "Win32",
            "Linux x86_64",
            "MacIntel",
        ]
        self.webgl_vendors = [
            "Intel Inc.",
            "NVIDIA Corporation",
            "AMD Inc.",
        ]
        self.renderers = [
            "Intel Iris OpenGL Engine",
            "GeForce GTX 1050 Ti/PCIe/SSE2",
            "AMD Radeon Pro 560X OpenGL Engine",
        ]

        self.q = Queue()
        self.is_running = False
        self.workers = workers

    def driverInit(self):

        user_agent = random.choice(self.user_agents)
        vendor = random.choice(self.vendors)
        platform = random.choice(self.platforms)
        webgl_vendor = random.choice(self.webgl_vendors)
        renderer = random.choice(self.renderers)

        server = Server(self.browsermob_proxy_path)
        server.start()
        proxy = server.create_proxy()
        proxy = server.create_proxy(params={"trustAllServers": "true"})

        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument(f"--proxy-server={proxy.proxy}")
        options.add_argument(f"user-agent={user_agent}")

        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-insecure-localhost")

        pem_file_path = os.path.abspath("my-ca.pem")
        options.add_argument(f"--ssl-key-log-file={pem_file_path}")

        driver = webdriver.Chrome(options=options)

        proxy.new_har("video", options={"captureContent": True})

        stealth(
            driver,
            languages=["en-US", "en"],
            vendor=vendor,
            platform=platform,
            webgl_vendor=webgl_vendor,
            renderer=renderer,
            fix_hairline=True,
        )
        return driver, proxy

    def check_ip(self):
        driver = self.driverInit()
        driver.get("https://api.ipify.org?format=json")
        time.sleep(20)
        ip_element = driver.find_element(By.TAG_NAME, "pre")
        ip_address = ip_element.text

        print("IP Address:", ip_address)

        driver.quit()

    def convert_m3u8_to_mp4(self, input_url, output_file):
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    input_url,
                    "-c",
                    "copy",
                    "-bsf:a",
                    "aac_adtstoasc",
                    output_file,
                ]
            )
            print(f"Conversion successful! Output file: {output_file}")
        except Exception as e:
            print(f"Error during conversion: {e}")

    def addToQueue(self, url):
        if self.is_running:
            self.q.put(url)
        else:
            self.startScraping([url])

    def worker(self):
        while True:
            url = self.q.get()
            if url is None:
                break
            self.getContents(url)
            self.q.task_done()

    def startScraping(self, urls):
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            self.is_running = True
            for _ in range(self.workers):
                executor.submit(self.worker)

            for url in urls:
                self.q.put(url)

            self.q.join()

            for _ in range(self.workers):
                self.q.put(None)
        self.is_running = False

    def jfifToJpeg(self, image, file_name):
        image = Image.open(BytesIO(image))
        image.save(file_name, "JPEG")

    def getContents(
        self,
        url,
    ):
        url = f"https://x.com{url}"
        wait_time = 15
        contents = {}
        driver, proxy = self.driverInit()
        driver.get(url)

        time.sleep(wait_time)
        post_id = url.split("/")[-1]
        if not os.path.exists(post_id):
            os.mkdir(post_id)
        out_path = f"./{post_id}"
        contents["PostId"] = post_id
        # text
        try:
            tweet_div = driver.find_element(By.XPATH, '//div[@data-testid="tweetText"]')
            tweet_text = tweet_div.text
            contents["tweet"] = tweet_text
        except Exception as e:
            print(f"guess no text?")

            html_content = driver.page_source
            with open(f"{out_path}/text_error.html", "w", encoding="utf-8") as file:

                file.write(html_content)

        # images
        images_names = []
        print(f"getting images of post: {post_id}...")
        for count in range(1, 5):
            try:
                img_a = driver.find_element(
                    By.XPATH, f'//a[@href="{url[13:]}/photo/{count}"]'
                )
            except:
                print("images get! ...or nah?")
                break
            img_img = img_a.find_element(By.TAG_NAME, "img")
            img_link = img_img.get_attribute("src")
            response = requests.get(img_link)

            file_name = f"{out_path}/{post_id}-{uuid.uuid4()}.jfif"

            self.jfifToJpeg(response.content, file_name)
            images_names.append(file_name)
        contents["images"] = images_names
        print("images saved")

        # html
        html_content = driver.page_source
        with open(f"{out_path}/{post_id}.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        contents["html"] = f"{post_id}.html"

        # VIDEOS
        videos_urls = []

        def scrollToEl(el, driver):
            driver.execute_script("arguments[0].scrollIntoView(true);", el)

        def pause_video(driver):
            video_pause = driver.find_element(By.XPATH, '//button[@aria-label="Pause"]')
            scrollToEl(video_pause, driver)
            video_pause.click()

        try:
            print("trying to get videos...")
            videos_el = driver.find_elements(By.TAG_NAME, "video")
            videos_el_len = len(videos_el)
            if videos_el_len > 1:

                pause_video(driver)
                for _ in range(5):
                    driver.find_element(By.TAG_NAME, "body").send_keys(
                        Keys.CONTROL, Keys.SUBTRACT
                    )
                print(f"video:{videos_el}")
                videos_el = videos_el[1:]

                for video_el in videos_el:
                    driver.execute_script(
                        "window.scrollTo(0, arguments[0].getBoundingClientRect().top + window.pageYOffset);",
                        video_el,
                    )
                    driver.execute_script("arguments[0].click();", video_el)
                    pause_video(driver)

            har_data = proxy.har
            m3u_url = None
            for entry in har_data["log"]["entries"]:
                request = entry["request"]
                if ".m3u8?" in request["url"]:
                    m3u_url = request["url"]
                    print(m3u_url)
                    videos_urls.append(m3u_url)
                    self.convert_m3u8_to_mp4(
                        m3u_url, f"{out_path}/{post_id}-{uuid.uuid1()}.mp4"
                    )
        except Exception as e:
            print(e)
            html_content = driver.page_source
            with open(f"{out_path}/videos_error.html", "w", encoding="utf-8") as file:
                file.write(html_content)
            contents["html"] = f"{post_id}.html"
            print(f"no video?")
        contents["video_urls"] = videos_urls

        # save the info
        file_name = "contents.json"
        temp = []
        if os.path.exists(file_name):
            with open(file_name, "r") as json_file:
                temp = json.load(json_file)

        temp.append(contents)

        with open(file_name, "w") as json_file:
            json.dump(temp, json_file, indent=4)

        with open("saved.txt", "a", encoding="utf-8") as file:
            file.write(f"\n{url[13:]}")
        driver.quit()
