# import aiohttp
# import asyncio
# import requests
# from concurrent.futures import ThreadPoolExecutor
# import time

# list_of_url = ["http://localhost:2000"] * 100


# def get_url(url):
#     return requests.get(url)


# start = time.time()
# with ThreadPoolExecutor(max_workers=4) as pool:
#     print(len(list(pool.map(get_url, list_of_url))))
# end = time.time()
# print("Took {} seconds to pull {} websites.".format(end - start, 0))


# websites = "http://localhost:2000\n" * 100


# async def get(url):
#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(url=url) as response:
#                 resp = await response.read()
#                 # print("Successfully got url {} with response of length {}.".format(url, len(resp)))
#     except Exception as e:
#         print("Unable to get url {} due to {}.".format(url, e.__class__))


# async def main(urls, amount):
#     ret = await asyncio.gather(*[get(url) for url in urls])
#     print("Finalized all. ret is a list of len {} outputs.".format(len(ret)))


# urls = websites.split("\n")
# amount = len(urls)

# start = time.time()
# asyncio.run(main(urls, amount))
# end = time.time()

# print("Took {} seconds to pull {} websites.".format(end - start, amount))
