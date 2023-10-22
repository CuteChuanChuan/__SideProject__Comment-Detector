import requests
from pprint import pprint
from loguru import logger
from bs4 import BeautifulSoup

response = requests.get(
    "https://www.ptt.cc/bbs/HatePolitics/M.1697964792.A.33F.html",
    cookies={"over18": "1"},
)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "lxml")
    prettified_html = soup.prettify()

    with open("for_parsing_article.html", "w", encoding="utf-8") as file:
        file.write(prettified_html)
else:
    print(f"Failed to retrieve the webpage. HTTP Status Code: {response.status_code}")
