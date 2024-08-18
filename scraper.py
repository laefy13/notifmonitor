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


from dbManager import DB
from monitor import profiler


class Scraper:
    def __init__(
        self,
        workers,
        max_retries,
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
        self.db = DB()
        self.max_retries = max_retries

        self.executor = ThreadPoolExecutor(max_workers=workers)
        self.keep_running = True
        self._start_worker_threads(workers)

    def _start_worker_threads(self, workers):
        for _ in range(workers):
            self.executor.submit(self.worker)

    def shutdown(self):

        self.keep_running = False
        print("Putting nones...")
        for _ in range(self.executor._max_workers):
            self.q.put(None)

        print("Waiting for other tasks to finish first...")
        self.executor.shutdown(wait=True)

    # @profiler
    def driverInit(self):

        user_agent = random.choice(self.user_agents)
        vendor = random.choice(self.vendors)
        platform = random.choice(self.platforms)
        webgl_vendor = random.choice(self.webgl_vendors)
        renderer = random.choice(self.renderers)

        server = Server(self.browsermob_proxy_path, options={"quiet": True})
        server.start()
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

    def checkIp(self):
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
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            print(f"Conversion successful! Output file: {output_file}")
        except Exception as e:
            print(f"Error during conversion: {e}")

    # @profiler
    def addToQueue(self, url):

        try:
            self.q.put(url)
            print("added to  queue")
        except Exception as e:
            print(f"add to q error: {e}")

    # @profiler
    def worker(self):
        try:

            while self.keep_running:
                print("u sure g that its blocked?")
                q_item = self.q.get()
                print("bruh is this real, like on a stack?")
                if q_item is None:
                    break
                try:
                    if isinstance(q_item, dict):
                        _, value = q_item.popitem()
                        if value == "image":
                            print("going to save images...")
                            self.saveImages(q_item)
                        elif value == "video":
                            print("going to save videos...")
                            self.saveVideos(q_item)
                        else:
                            print("how")

                    self.getContents(q_item)
                    print(f"{q_item}, task done")
                finally:
                    self.q.task_done()
                    print(f"{q_item}, task done nahh thas frfr ong")
            print("worker 2 Queue contents:", list(self.q.queue))

        except Exception as e:
            print(f"worker error: {e}")

    def jfifToJpeg(self, image, file_name):
        image = Image.open(BytesIO(image))
        image.save(file_name, "JPEG")

    def isSaved(self, url):
        if self.db.urlSaved(url):
            return True
        return False

    def saveImages(self, image_urls: dict):
        print("inside save images func...")
        for file_name, img_link in image_urls.items():
            response = requests.get(img_link)
            self.jfifToJpeg(response.content, file_name)

    def saveVideos(self, video_urls: dict):
        print("inside save videos func...")
        for file_name, video_link in video_urls:
            self.convert_m3u8_to_mp4(video_link, file_name)

    @profiler
    def getContents(
        self,
        url,
    ):
        try:
            if self.db.urlSaved(url):
                print(f"{url} is already saved! ")
                return
            url_split = url.split("/")
            profile_name = url_split[1]
            print(url_split)
            post_id = url_split[-1]
            out_path = os.path.join(profile_name, post_id)
            if not os.path.exists(out_path):
                os.makedirs(out_path)
            print(f"outpath: {out_path}")

            url = f"https://x.com{url}"
            wait_time = 15
            contents = {}
            driver, proxy = self.driverInit()
            driver.get(url)

            time.sleep(wait_time)

            # post not found / deleted or account is private or internet issues:
            for _ in range(self.max_retries):
                try:
                    reloading_element = driver.find_element(
                        By.XPATH,
                        '//span[contains(text(), "Something went wrong. Try reloading.")]',
                    )
                    if reloading_element:
                        print(
                            "post not found / deleted or account is private or internet issues!"
                        )
                        driver.refresh()
                except:
                    print("post found!")
                    break

            contents["PostId"] = post_id

            # text
            try:
                tweet_div = driver.find_element(
                    By.XPATH, '//div[@data-testid="tweetText"]'
                )
                tweet_text = tweet_div.text
                contents["tweet"] = tweet_text
            except Exception as e:
                print(f"guess no text?")

                html_content = driver.page_source
                with open(f"{out_path}/text_error.html", "w", encoding="utf-8") as file:

                    file.write(html_content)

            # images
            image_urls = {}
            print(f"getting images of post: {post_id}...")
            for count in range(1, 5):
                try:
                    img_a = driver.find_element(
                        By.XPATH, f'//a[@href="{url[13:]}/photo/{count}"]'
                    )
                except:
                    if count > 1:
                        print("images get! ...or nah?")
                    if count < 2:
                        print("no images! i think")
                    break
                img_img = img_a.find_element(By.TAG_NAME, "img")
                img_link = img_img.get_attribute("src")
                file_name = os.path.join(out_path, f"{post_id}-{uuid.uuid4()}.jpg")

                image_urls[file_name] = img_link

            contents["images"] = image_urls
            if image_urls:
                image_urls["__type__"] = "image"
                self.q.put(image_urls)

            # html
            html_content = driver.page_source
            with open(
                os.path.join(out_path, f"{post_id}.html"), "w", encoding="utf-8"
            ) as file:
                file.write(html_content)
            contents["html"] = f"{post_id}.html"

            # VIDEOS
            def scrollToEl(el, driver):
                driver.execute_script("arguments[0].scrollIntoView(true);", el)

            def pause_video(driver):
                video_pause = driver.find_element(
                    By.XPATH, '//button[@aria-label="Pause"]'
                )
                scrollToEl(video_pause, driver)
                video_pause.click()

            video_urls = {}
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

                        video_urls[
                            os.path.join(out_path, f"{post_id}-{uuid.uuid1()}.mp4")
                        ] = m3u_url

            except Exception as e:
                html_content = driver.page_source
                with open(
                    os.path.join(out_path, f"videos_error.html"), "w", encoding="utf-8"
                ) as file:
                    file.write(html_content)
                print(f"no video?")
            contents["video_urls"] = video_urls
            if video_urls:
                video_urls["__type__"] = "video"
                self.q.put(video_urls)

            # save the info
            file_name = os.path.join(out_path, "contents.json")
            temp = []
            if os.path.exists(file_name):
                with open(file_name, "r") as json_file:
                    temp = json.load(json_file)

            temp.append(contents)
            with open(file_name, "w") as json_file:
                json.dump(temp, json_file, indent=4)

            self.db.insert(url)

            driver.quit()
            proxy.close()
            print("driver quit and proxy off")
        except Exception as e:
            driver.quit()
            proxy.close()
            print("driver quit and proxy off but error")
            print(f"cnontents error: {e}")
