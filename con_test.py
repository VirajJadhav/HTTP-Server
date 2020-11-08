# import aiohttp
# import asyncio
# import requests
# from concurrent.futures import ThreadPoolExecutor
# import time

# list_of_url = ["/ClientFiles/new.txt", "/", "/form.html",
#                "/", "/form.html", "/ClientFiles/new.txt"]

# index = [i for i in range(6)]


# def get_url(url, index):
#     final = "http://localhost:2000"
#     if url != "/":
#         final += url
#     if index == 0:
#         return requests.delete(final)
#     elif index == 1 or index == 2:
#         return requests.get(final)
#     elif index == 3:
#         d = {
#             'book': "viraj"
#         }
#         return requests.post(final, data=d)
#     elif index == 4:
#         return requests.head(final)
#     else:
#         d = {
#             'book': "viraj"
#         }
#         return requests.put(final, data=d)


# start = time.time()
# with ThreadPoolExecutor(max_workers=500) as pool:
#     print(len(list(pool.map(get_url, list_of_url, index))))
# end = time.time()
# print("Took {} seconds.".format(end - start))


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
