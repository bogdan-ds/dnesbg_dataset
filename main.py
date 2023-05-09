import json
import os
import random
import re
import time

from bs4 import BeautifulSoup

from utils.request_generator import Request


class ResumableScraper:

    def __init__(self, proxify: bool = False):
        self.proxify = proxify
        self.progress = self.load_saved_progress()

    @staticmethod
    def load_saved_progress():
        if not os.path.exists("progress.json"):
            return {"last_page": 1, "article_ids": []}

        with open("progress.json", "r") as f:
            return json.load(f)

    def save_progress(self):
        with open("progress.json", "w") as f:
            json.dump(self.progress, f)

    def check_if_id_is_processed(self, article_id: int) -> bool:
        return article_id in self.progress["article_ids"]


class DnesArticleScraper(ResumableScraper):

    def __init__(self, proxify: bool = False, page_start: int = 0,
                 page_end: int = 5):
        super().__init__(proxify)
        self.page_start = page_start
        self.page_end = page_end
        self.main_url = "https://www.dnes.bg/news.php?last&cat=1&page="

    def run(self):
        for page_id in range(self.progress["last_page"], self.page_end + 1):
            articles = self.get_articles(page_id)
            for article_id, article_url in articles.items():
                self.save_article_to_file(article_id, article_url)
            self.progress["last_page"] = page_id
            self.save_progress()

    def get_articles(self, page_id: int) -> dict:
        request = Request(proxify=self.proxify)
        response = request.get(self.main_url + str(page_id))
        articles = self.parse_article_pages(response.text)
        return articles

    @staticmethod
    def parse_article_pages(page_html: str) -> dict:
        parsed_html = BeautifulSoup(page_html, "html.parser")
        comment_links = parsed_html.body.find_all("a", attrs={"class": "com"})
        articles = dict()
        for comment in comment_links:
            if int(comment.text) > 5:
                articles_regex = '(/.*?)\.(\d+)\#comments'
                matches = re.search(articles_regex, comment["href"])
                if matches:
                    articles[matches.group(2)] = matches.group(0)
        return articles

    @staticmethod
    def save_article_to_file(article_id: int, article_url: str):
        with open(f"output/article_list.csv", "a") as f:
            f.write(f"{article_id},{article_url}\n")


class DnesCommentScraper(ResumableScraper):

    def __init__(self, proxify: bool = False):
        super().__init__(proxify)
        self.main_url = "https://www.dnes.bg"

    def process_articles(self) -> None:
        with open("output/article_list.csv", "r") as f:
            for line in f:
                article_id, article_url = line.split(",")
                article_url = article_url.strip()
                article_url = article_url.replace("#comments", "")
                if not self.check_if_id_is_processed(article_id):
                    print(f"Processing article {article_id}...")
                    article_html = self.get_article_html(
                        self.main_url + article_url)
                    page_navigation = self.get_comment_page_navigation(
                        article_html)
                    counter = 0
                    if page_navigation:
                        page_navigation = range(1, max(page_navigation) + 1)
                        for page in page_navigation:
                            time.sleep(random.randint(0, 2))
                            page_html = self.get_article_html(
                                self.main_url + article_url + f",{page}")
                            saved = self.extract_and_save_contents(page_html)
                            counter += saved
                    else:
                        saved = self.extract_and_save_contents(article_html)
                        counter += saved
                    self.progress["article_ids"].append(article_id)
                    self.save_progress()
                    print(f"Saved {counter} comments for article {article_id}.")

    def get_article_html(self, article_url: str) -> str:
        print(f"Getting {article_url}...")
        request = Request(proxify=self.proxify)
        response = request.get(article_url)
        return response.text

    @staticmethod
    def get_comment_page_navigation(page_html: str) -> list:
        parsed_html = BeautifulSoup(page_html, "html.parser")
        page_navigation = parsed_html.body.find_all(
            "div", attrs={"class": "comments-pagging"})
        pages = list()
        if page_navigation:
            all_elements = page_navigation[0].find_all("a")
            for element in all_elements:
                if element.text.isdigit():
                    pages.append(int(element.text))
        return pages

    def extract_and_save_contents(self, page_html: str):
        parsed_html = BeautifulSoup(page_html, "html.parser")
        comments = parsed_html.body.find_all("div",
                                             attrs={"class": "commen_cont"})
        counter = 0
        for comment in comments:
            author = comment.find("div", attrs={"class": "comment_user"}).text
            author = self.sanitize_author(author)
            up_votes = comment.find(
                "span",
                attrs={"class": "comments-grade comments-grades-up"}).text
            down_votes = comment.find(
                "span",
                attrs={"class": "comments-grade comments-grades-down"}).text
            comment_text = comment.find("div",
                                        attrs={"class": "comment_text"}).text
            comment_text = self.sanitize_comment_text(comment_text)
            counter += 1
            self.save_comment_to_file(author, up_votes,
                                      down_votes, comment_text)
        return counter

    @staticmethod
    def sanitize_author(author: str) -> str:
        author = author.split(" ")[0]
        for char in ["\n", ",", "\""]:
            author = author.replace(char, "")
        return author

    @staticmethod
    def sanitize_comment_text(comment_text: str) -> str:
        comment_text = comment_text.strip()
        comment_text = comment_text.replace(
            " Сигнализирахте за неуместен коментар", "")
        comment_text = comment_text.replace("\"", "")
        return comment_text

    @staticmethod
    def save_comment_to_file(author, up_votes, down_votes, comment_text):
        new_file = not os.path.exists("output/comment_list.csv")
        with open(f"output/comment_list.csv", "a") as f:
            if new_file:
                f.write("author,up_votes,down_votes,comment_text\n")
            f.write(f"\"{author}\",\"{up_votes}\","
                    f"\"{down_votes}\",\"{comment_text}\"\n")
