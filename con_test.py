# import aiohttp
# import asyncio
import requests
from concurrent.futures import ThreadPoolExecutor
import time

# list_of_urls = ["/ClientFiles/new.txt", "/", "/form.html",
#                 "/", "/form.html", "/ClientFiles/new.txt"]

# index = [i for i in range(6)]

testCases = []
list_of_urls = []
methods = []

with open("test.txt", "r") as f:
    testCases = f.read().split("#" * 30)

for test in testCases:
    data = test.lstrip("\n").split("\n")[0].split(" ")
    if len(data) > 1:
        methods.append(data[0])
        list_of_urls.append(data[1])


def get_url(url, method):
    final = "http://localhost:2000"
    if url != "/":
        final += url
    if method == "GET":
        return requests.get(final)
    elif method == "POST":
        d = {
            'book': "viraj"
        }
        return requests.post(final, data=d)
    elif method == "PUT":
        d = {
            'book': "viraj"
        }
        return requests.put(final, data=d)
    elif method == "HEAD":
        return requests.head(final)
    elif method == "DELETE":
        return requests.delete(final)


start = time.time()
with ThreadPoolExecutor(max_workers=500) as pool:
    print(len(list(pool.map(get_url, list_of_urls, methods))))
end = time.time()
print("Took {} seconds.".format(end - start))
