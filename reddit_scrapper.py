import asyncio

from bs4 import BeautifulSoup
from datetime import datetime
import requests
import uuid
import logging

LOG_LEVEL = "DEBUG"
OLD_REDDIT_BASE_URL = "https://old.reddit.com"
USER_AGENT_HEADER = {'User-agent': 'your bot 0.1'}  # prevents 429


async def scrap_posts_into_file(posts_amount=100):
    logging.basicConfig(level=LOG_LEVEL)
    logging.info("Creating file...")
    filename = "./results/reddit-" + datetime.now().strftime("%Y%m%d%H%M") + ".txt"
    with open(filename, "w", encoding='utf-8') as file:
        try:
            page = do_get(OLD_REDDIT_BASE_URL + "/top/?t=month&limit=" + str(posts_amount))
            soup = BeautifulSoup(page.content, 'html.parser')
            posts = soup.find_all("div", class_="thing")

            coroutines = [__scrap_data(file, post) for post in posts]
            await asyncio.gather(*coroutines)

            return filename
        finally:
            logging.info("Closing file...")
            file.close()


async def __scrap_data(file, post):
    date, post_url, category, comments_num, author, votes_num = __scrap_post_data(post)
    try:
        cake_day, comment_karma, post_karma, user_karma = await __scrap_user_data(author)
        file.write("UUID=" + uuid.uuid4().hex + ";" +
                   "POST_URL=" + post_url + ";" +
                   "AUTHOR=" + author + ";" +
                   "USER_KARMA=" + user_karma + ";" +
                   "CAKE_DAY=" + cake_day + ";" +
                   "POST_KARMA=" + post_karma + ";" +
                   "COMMENT_KARMA=" + comment_karma + ";" +
                   "DATE=" + date + ";" +
                   "COMMENTS_AMOUNT=" + comments_num + ";" +
                   "VOTES_AMOUNT=" + votes_num + ";" +
                   "CATEGORY=" + category + ";\n")
    except Exception as e:
        logging.warning("Userdata could not be scrapped, skipping post...")
        logging.debug(str(e))


async def __scrap_user_data(author):
    page_url = OLD_REDDIT_BASE_URL + "/user/" + author

    loop = asyncio.get_event_loop()
    page = await loop.run_in_executor(None, do_get, page_url)

    soup = BeautifulSoup(page.content, 'html.parser')

    post_karma = soup.find("span", class_="karma").contents[0]
    comment_karma = soup.find("span", class_="comment-karma").contents[0]
    cake_day = soup.find("time")['datetime']
    user_karma = str(int(post_karma.replace(',', '')) + int(comment_karma.replace(',', '')))
    return cake_day, comment_karma, post_karma, user_karma


def __scrap_post_data(post):
    return str(datetime.fromtimestamp((int(post['data-timestamp']) / 1000))), \
           OLD_REDDIT_BASE_URL + post['data-permalink'], \
           post['data-subreddit-prefixed'], \
           post['data-comments-count'], \
           post['data-author'], \
           post['data-score'],


def do_get(url):
    return requests.get(url, headers=USER_AGENT_HEADER)
