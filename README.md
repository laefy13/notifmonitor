
# Notification Monitor

^ _ ^ This is only for education purposes ^ _ ^

Basically a script that will monitor the log file of the Chrome (specifically C:\Users\user\AppData\Local\Google\Chrome\User Data\Default\Platform Notifications\000003.log). The information that is added to this file are notifications only (haven't tested other chrome things so yeah). If you enabled the push notification of a certain website, then you have a notification on for some profiles, and if they posted, the script should save the information within the post, such as the text, images, video and the html file itself. 




## Restrictions!

- the following aren't tested since I don't encounter this, but will update if I do, prolly
- Other notifications from Chrome (this should be fine since the script filters for a regular expression for a certain site, so unless the format is the same that certain site, everything should be fine)
- Two or more posts that has video at the same time



## Dependencies

- Java Version 8 build 1.8.0_421-b09 (is what I use but as long as browsermob runs any ver is fine)
- [browsermob](https://github.com/lightbody/browsermob-proxy)
- [cert](https://github.com/lightbody/browsermob-proxy?tab=readme-ov-file#ssl-support)

## Run Locally

Clone the project

```bash
  git clone https://github.com/laefy13/notifmonitor
```

Go to the project directory

```bash
  cd notifmonitor
```

Install dependencies

```bash
  pip install selenium_stealth requests
```
Run script (these two should be run in two different consoles)
```bash
  python browsermob.py --path D:\path\to\browsermob-proxy-2.1.4\lib
```
```bash
  python main.py --path C:\Users\path\to\log --bmob-path D:\path\to\browsermob-proxy-2.1.4\bin\browsermob-proxy
```



