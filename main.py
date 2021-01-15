from bs4 import BeautifulSoup
from datetime import datetime
import requests
import uuid
import logging

LOG_LEVEL = "DEBUG"
OLD_REDDIT_BASE_URL = "https://old.reddit.com"
USER_AGENT_HEADER = {'User-agent': 'your bot 0.1'}  # prevent 429


def main():
    logging.basicConfig(level=LOG_LEVEL)
    logging.info("Creating file...")
    filename = "./results/reddit-" + datetime.now().strftime("%Y%m%d%H%M") + ".txt"
    with open(filename, "w", encoding='utf-8') as file:
        try:
            page = requests.get(OLD_REDDIT_BASE_URL + "/top/?t=month&limit=100", headers=USER_AGENT_HEADER)
            soup = BeautifulSoup(page.content, 'html.parser')
            posts_divs = soup.find_all("div", class_="thing")
            for post_div in posts_divs:
                username, comments_amount, category, date, post_url, votes_amount = scrap_post_data(post_div)
                try:
                    user_page_url = OLD_REDDIT_BASE_URL + "/user/" + username
                    old_author_page = requests.get(user_page_url, headers=USER_AGENT_HEADER)
                    old_author_page_soup = BeautifulSoup(old_author_page.content, 'html.parser')

                    cake_day, comment_karma, post_karma, user_karma = scrap_user_data(old_author_page_soup)
                except Exception as e:
                    logging.warning("Some data could not be scrapped, skipping post...")
                    logging.debug(str(e))

                file.write("UUID=" + uuid.uuid4().hex + ";" +
                           "POST_URL=" + post_url + ";" +
                           "AUTHOR_USERNAME=" + username + ";" +
                           "USER_KARMA=" + user_karma + ";" +
                           "CAKE_DAY=" + cake_day + ";" +
                           "POST_KARMA=" + post_karma + ";" +
                           "COMMENT_KARMA=" + comment_karma + ";" +
                           "POST_DATE=" + date + ";" +
                           "COMMENT_AMOUNT=" + comments_amount + ";" +
                           "VOTES_AMOUNT=" + votes_amount + ";" +
                           "POST_CATEGORY=" + category + ";\n")
        finally:
            logging.info("Closing file...")
            file.close()


def scrap_post_data(post_div):
    post_url = OLD_REDDIT_BASE_URL + post_div['data-permalink']
    author_username = post_div['data-author']
    post_date = post_div['data-timestamp']
    comments_amount = post_div['data-comments-count']
    votes_amount = post_div['data-score']
    post_category = post_div['data-subreddit-prefixed']
    return author_username, comments_amount, post_category, post_date, post_url, votes_amount


def scrap_user_data(old_author_page_soup):
    post_karma = old_author_page_soup.find("span", class_="karma").contents[0]
    comment_karma = old_author_page_soup.find("span", class_="comment-karma").contents[0]
    cake_day = old_author_page_soup.find("time")['datetime']

    post_karma_int = int(str(post_karma).replace(',', ''))
    comment_karma_int = int(str(comment_karma).replace(',', ''))
    user_karma = str(post_karma_int + comment_karma_int)

    return cake_day, comment_karma, post_karma, user_karma


if __name__ == '__main__':
    main()
