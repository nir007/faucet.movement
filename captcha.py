import asyncio
import http.client

from aiohttp import ClientSession

class RecaptchaV2Solver():
    __base_api_url = "https://api.capmonster.cloud"
    __pay_url = "https://capmonster.cloud/SelectPaymentType"
    __create_task_path = "/createTask"
    __get_task_result_path = "/getTaskResult"
    __captcha_api_key: str
    __site_url: str
    __site_key: str
    __proxy: str

    def __init__(self, session: ClientSession, proxy: str, site_url: str, site_key: str, client_key: str):
        self.__captcha_api_key = client_key
        self.__site_url = site_url
        self.__site_key = site_key
        self.__session = session
        self.__proxy = proxy

    @staticmethod
    def make_url(base: str, path: str):
        return f"{base}{path}"

    async def __make_request(self, *, method: str = "GET", url: str, body: {}):
        async with self.__session.request(
                method=method,
                url=url,
                headers={
                    "Content-Type": "application/json; charset=utf-8"
                },
                json=body
        ) as response:
            if response.status in (http.client.OK, http.client.CREATED):
                return await response.json(content_type=response.headers["Content-Type"]), response.status

            return None, response.status

    async def create_captcha_task(self) -> str | None:
        payload = {
            "clientKey": self.__captcha_api_key,
            "task": {
                "type": "RecaptchaV2Task" if self.__proxy else "RecaptchaV2TaskProxyless",
                "websiteURL": self.__site_url,
                "websiteKey": self.__site_key,
                "userAgent": self.__session.headers["User-Agent"]
            }
        }

        if self.__proxy:
            proxy_tuple = self.__proxy.split("@")

            proxy_login, proxy_pass = proxy_tuple[0].split(":")
            proxy_addr, proxy_port = proxy_tuple[1].split(":")

            payload["task"].update({
                "proxyType": "http",
                "proxyAddress": proxy_addr,
                "proxyPort": proxy_port,
                "proxyLogin": proxy_login,
                "proxyPassword": proxy_pass,
            })

        response, http_code = await self.__make_request(
            method="POST",
            body=payload,
            url=self.make_url(self.__base_api_url, self.__create_task_path)
        )

        if http_code == http.client.PAYMENT_REQUIRED:
            raise RuntimeError(f"Top up your balance captcha API. \n{self.__pay_url}")

        if http_code not in (http.client.OK, http.client.CREATED):
            raise RuntimeError(f"Bad response {http_code}")

        if response["errorId"] == 0:
            return response["taskId"]

        raise RuntimeError(f"Error: {response["errorDescription"]}")

    async def get_captcha_token(self, task_id: str):
        payload = {
            "clientKey": self.__captcha_api_key,
            "taskId": task_id
        }

        total_time = 0
        timeout = 360
        sleep = 5

        while True:
            response, http_code = await self.__make_request(
                method="POST",
                body=payload,
                url=self.make_url(self.__base_api_url, self.__get_task_result_path)
            )

            if http_code != http.client.OK:
                raise RuntimeError(f"Can`t check status. Bad response {http_code}")

            if response["status"] == "ready":
                return response["solution"]["gRecaptchaResponse"]

            total_time += sleep
            await asyncio.sleep(sleep)

            if timeout < total_time:
                raise RuntimeError(f"Can`t get captcha token in {timeout} seconds")
