import random
import requests
import logging
from utils.user_agents import user_agents_list

logger = logging.getLogger(__name__)


class Request:

    def __init__(self, proxify: bool = False):
        self.proxify = proxify
        self.headers = None
        self.proxies = {}
        user_agent = self.select_user_agent()
        self.headers = {
            'User-Agent': user_agent,
            'Content-type': 'application/x-www-form-urlencoded; '
                            'charset=windows-1251',
            'Accept-Language': 'en-US,en;q=0.9,bg;q=0.8,de;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        # if self.proxify:
        #     self.set_proxy()

    def select_user_agent(self) -> str:
        rand_element = random.randrange(0, len(user_agents_list))
        return user_agents_list[rand_element]

    def set_proxy(self, ip: str, port: str) -> None:
        if self.proxify:
            self.proxies = {
                "https": f"{ip}:{port}"
            }

    def get(self, url: str, timeout: int = 10) -> requests.Response:
        try:
            response = requests.get(url,
                                    headers=self.headers,
                                    proxies=self.proxies,
                                    timeout=timeout)
            if response.status_code == 200:
                return response
            else:
                logger.info(
                    f"Unexpected status code when making "
                    f"GET request to {url}: {response.status_code}")

        except Exception as e:
            logger.info(f"Could not make GET request to {url}, exception {e}")
            raise

    def post(self, url: str, data: dict,
             timeout: int = 10) -> requests.Response:
        try:
            response = requests.post(url,
                                     data=data,
                                     headers=self.headers,
                                     proxies=self.proxies,
                                     timeout=timeout)
            return response
        except Exception as e:
            logger.info(f"Could not make POST request to {url}, exception {e}")
            raise
