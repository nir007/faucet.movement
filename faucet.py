import http.client
from aiohttp import ClientSession
from captcha import RecaptchaV2Solver

class MovementFaucet:
    __faucet_url = "https://mevm.devnet.imola.movementlabs.xyz/"
    __session: ClientSession
    __captcha_solver: RecaptchaV2Solver

    def __init__(
            self,
            cli_session: ClientSession,
            proxy: str,
            site_url: str,
            site_key: str,
            captcha_api_key: str
    ):
        self.__session = cli_session

        self.__captcha_solver = RecaptchaV2Solver(
            session=self.__session,
            client_key=captcha_api_key,
            site_key=site_key,
            site_url=site_url,
            proxy=proxy
        )

    async def claim_move(self, *, address: str) -> bool:
        task_id = await self.__captcha_solver.create_captcha_task()

        print(f"Task created with id: {task_id}")

        token = await self.__captcha_solver.get_captcha_token(
            task_id=task_id
        )

        if token is None:
            raise RuntimeError("Can`t solve captcha")

        print(f"Task solved with token: {token}")

        payload = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "eth_batch_faucet",
            "params": [address]
        }

        async with self.__session.request(
            method="POST",
            url=self.__faucet_url,
            json=payload,
            headers={
                "Token": token
            }
        ) as response:
            if response.status != http.client.OK:
                raise RuntimeError(f"Bad response from faucet: {response.status}")

        return True