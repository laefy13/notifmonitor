"""
Run this script only when you want to save the current contents
of the log file to the saved.txt file.
Make sure to change the log_file_path
"""

import re

pattern2 = r"/[^/]+?/status/\d+"

log_file_path = r"C:\Users\fy\AppData\Local\Google\Chrome\User Data\Default\Platform Notifications\000003.log"
with open(log_file_path, "r", encoding="iso-8859-15") as file:
    new_content = file.read()
    matches2 = re.findall(pattern2, new_content)
    matches_str = "\n".join(matches2)
    print(matches_str)
    with open("saved.txt", "w", encoding="utf-8") as file:
        file.write(matches_str)
    print(f"matches 2 len {len(matches2)}")
