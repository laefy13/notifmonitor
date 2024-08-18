from dbManager import DB
import re

db = DB()

pattern2 = r"/[^/]+?/status/\d+"

log_file_path = r"C:\Users\fy\AppData\Local\Google\Chrome\User Data\Default\Platform Notifications\000004.log"
with open(log_file_path, "r", encoding="iso-8859-15") as file:
    new_content = file.read()
    matches2 = re.findall(pattern2, new_content)
    db.insertMany(matches2)
    print(f"matches 2 len {len(matches2)}")
