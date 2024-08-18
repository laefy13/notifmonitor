
# Notification Monitor

^ _ ^ This is only for education purposes ^ _ ^

Basically a script that will monitor the log file of the Chrome (specifically C:\Users\user\AppData\Local\Google\Chrome\User Data\Default\Platform Notifications\000003.log). The information that is added to this file are notifications only (haven't tested other chrome things so yeah). If you enabled the push notification of a certain website, then you have a notification on for some profiles, and if they posted, the script should save the information within the post, such as the text, images, video and the html file itself. 

## updates

* 8/19/24
  * monitor.py for profiling decorators of functions, uncomment or put one to any function
  * changed the saving of the saved urls from text to db 
  * db_read.py to be used instead of read.py for saving all of the urls in the current log.
  * add a new arg for main.py, --max-retries, to allow reloading of the pages if the user has goofy internet
  * Made so that the pool is always open for possible job
  * the previous pushed one was kinda working but at the same time no so yeah


## Restrictions!

- the following aren't tested since I don't encounter this, but will update if I do, prolly
- Other notifications from Chrome (this should be fine since the script filters for a regular expression for a certain site, so unless the format is the same that certain site, everything should be fine)
- Two or more posts that has video at the same time
- Can't access private profiles, unless you declare the profile of the chrome to be used in options



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
Run script
```bash
  python main.py --workers 1 --path C:\Users\path\to\log --bmob-path D:\path\to\browsermob-proxy-2.1.4\bin\browsermob-proxy
```



