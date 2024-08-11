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


class Scraper:
    def __init__(
        self,
        bmob_path=r"C:\Users\fy\Desktop\browsermob-proxy-2.1.4\bin\browsermob-proxy",
    ):
        browsermob_proxy_path = bmob_path
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]

        vendors = [
            "Google Inc.",
            "Mozilla Foundation",
            "Microsoft Corporation",
        ]
        platforms = [
            "Win32",
            "Linux x86_64",
            "MacIntel",
        ]
        webgl_vendors = [
            "Intel Inc.",
            "NVIDIA Corporation",
            "AMD Inc.",
        ]
        renderers = [
            "Intel Iris OpenGL Engine",
            "GeForce GTX 1050 Ti/PCIe/SSE2",
            "AMD Radeon Pro 560X OpenGL Engine",
        ]

        user_agent = random.choice(user_agents)
        vendor = random.choice(vendors)
        platform = random.choice(platforms)
        webgl_vendor = random.choice(webgl_vendors)
        renderer = random.choice(renderers)

        server = Server(browsermob_proxy_path)
        server.start()
        self.proxy = server.create_proxy()
        self.proxy = server.create_proxy(params={"trustAllServers": "true"})

        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_argument(f"--proxy-server={self.proxy.proxy}")
        options.add_argument(f"user-agent={user_agent}")

        options.add_argument("--headless")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-insecure-localhost")

        pem_file_path = os.path.abspath("my-ca.pem")
        options.add_argument(f"--ssl-key-log-file={pem_file_path}")

        self.driver = webdriver.Chrome(options=options)

        self.proxy.new_har("video", options={"captureContent": True})

        stealth(
            self.driver,
            languages=["en-US", "en"],
            vendor=vendor,
            platform=platform,
            webgl_vendor=webgl_vendor,
            renderer=renderer,
            fix_hairline=True,
        )

        self.q = Queue()
        self.is_running = False

    def check_ip(self):
        self.driver.get("https://api.ipify.org?format=json")
        time.sleep(20)
        ip_element = self.driver.find_element(By.TAG_NAME, "pre")
        ip_address = ip_element.text

        print("IP Address:", ip_address)

        self.driver.quit()

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

    def driverExit(self):
        print("exiting driver...")
        self.driver.quit()

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
        with ThreadPoolExecutor(max_workers=5) as executor:
            self.is_running = True
            for _ in range(5):
                executor.submit(self.worker)

            for url in urls:
                self.q.put(url)

            self.q.join()

            for _ in range(5):
                self.q.put(None)
        self.is_running = False

    def getContents(
        self,
        url,
    ):
        url = f"https://x.com{url}"
        wait_time = 15
        print("url:", url)
        contents = {}

        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[-1])
        self.driver.get(url)
        time.sleep(wait_time)
        post_id = url.split("/")[-1]
        if not os.path.exists(post_id):
            os.mkdir(post_id)
        out_path = f"./{post_id}"
        contents["PostId"] = post_id
        # text
        try:
            tweet_div = self.driver.find_element(
                By.XPATH, '//div[@data-testid="tweetText"]'
            )
            tweet_text = tweet_div.text
            contents["tweet"] = tweet_text
        except Exception as e:
            print(f"guess no text?")

            html_content = self.driver.page_source
            with open(f"{out_path}/text_error.html", "w", encoding="utf-8") as file:

                file.write(html_content)

        # images
        images_names = []
        print(f"getting images of post: {post_id}...")
        for count in range(1, 5):
            try:
                img_a = self.driver.find_element(
                    By.XPATH, f'//a[@href="{url[13:]}/photo/{count}"]'
                )
            except:
                print("images get! ...or nah?")
                break
            img_img = img_a.find_element(By.TAG_NAME, "img")
            img_link = img_img.get_attribute("src")
            response = requests.get(img_link)

            file_name = f"{post_id}-{uuid.uuid4()}.jfif"
            with open(f"{out_path}/{file_name}", "wb") as file:
                file.write(response.content)
            images_names.append(file_name)
        contents["images"] = images_names
        print("images saved")

        # html
        html_content = self.driver.page_source
        with open(f"{post_id}.html", "w", encoding="utf-8") as file:
            file.write(html_content)
        contents["html"] = f"{post_id}.html"

        # VIDEOS
        videos_urls = []

        def pause_video(driver):
            video_pause = driver.find_element(By.XPATH, '//button[@aria-label="Pause"]')
            video_pause.click()

        try:
            print("trying to get videos...")
            pause_video(self.driver)
            videos_el = self.driver.find_elements(By.TAG_NAME, "video")
            # the first video is cut cuz it should auto play when the device is desktop
            videos_el = videos_el[1:]

            for video_el in videos_el:
                video_el.click()
                pause_video(self.driver)

            har_data = self.proxy.har
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
            html_content = self.driver.page_source
            with open(f"{out_path}/videos_error.html", "w", encoding="utf-8") as file:
                file.write(html_content)
            contents["html"] = f"{post_id}.html"
            print(f"no video?")
        contents["video_urls"] = videos_urls

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

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
