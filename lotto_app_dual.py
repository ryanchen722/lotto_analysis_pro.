import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

BASE_URL = "https://www.pilio.idv.tw/lto539/drawlist/drawlist.asp?page={}"

history = []

page = 1

while True:

    url = BASE_URL.format(page)
    print("抓取第", page, "頁")

    r = requests.get(url, timeout=10)
    r.encoding = "utf-8"

    soup = BeautifulSoup(r.text, "lxml")

    table = soup.find("table")

    if not table:
        break

    rows = table.find_all("tr")

    count_this_page = 0

    for row in rows:

        cols = row.find_all("td")

        if len(cols) >= 5:

            nums = []

            for col in cols:

                text = col.text.strip()

                if text.isdigit():

                    n = int(text)

                    if 1 <= n <= 39:

                        nums.append(n)

            if len(nums) == 5:

                history.append(sorted(nums))

                count_this_page += 1

    if count_this_page == 0:
        break

    page += 1

    time.sleep(0.5)

print("總共抓到期數:", len(history))

df = pd.DataFrame(history, columns=["n1","n2","n3","n4","n5"])

df.to_csv("539_history.csv", index=False)

print("已存成 539_history.csv")