import asyncio

from src.intergrations import yandex_search_api


async def main() -> None:
  print(await yandex_search_api.search_async("Что такое таксономия блума?"))


asyncio.run(main())
