import asyncio
import os
import random
from dotenv import load_dotenv
from aiohttp import ClientSession, TCPConnector
from aiohttp_socks import ProxyConnector
from faucet import MovementFaucet


def get_user_agent() -> str:
    random_version = f"{random.uniform(520, 540):.2f}"
    return (f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            f"AppleWebKit/{random_version} (KHTML, like Gecko) "
            f"Chrome/129.0.0.0 Safari/{random_version}")

async def main():
    load_dotenv()

    proxy = os.getenv('PROXY')
    captcha_api_key = os.getenv('CAPTCHA_API_KEY')
    site_url = os.getenv('SITE_URL')
    site_key = os.getenv('SITE_KEY')

    address = input("Enter your address: ")

    session = ClientSession(
        connector=ProxyConnector.from_url(
            f"http://{proxy}") if proxy else TCPConnector(),
            headers={"User-Agent": get_user_agent()}
    )

    try:
        faucet = MovementFaucet(
            cli_session=session,
            site_url=site_url,
            site_key=site_key,
            proxy=proxy,
            captcha_api_key=captcha_api_key
        )

        if await faucet.claim_move(address=address):
            print(f"Success! Check your wallet {address}")

    except Exception as e:
        print(f"Something went wrong: {e}")
    finally:
        await session.close()


asyncio.run(main())
