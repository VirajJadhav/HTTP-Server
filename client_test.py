import requests
import json
from configparser import ConfigParser
import sys
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import time

CONFIG = None

DEBUG = False


def readTestFile(fileName=""):
    testCases = []
    with open(fileName, "r") as f:
        testCases = json.load(f)
    return testCases


def loadThreads(case={}, method="", finalurl=""):
    global DEBUG
    response = b''
    try:
        if method == "GET":
            if "headers" in case:
                headers = case["headers"]
                response = requests.get(finalurl, headers=headers)
            else:
                response = requests.get(finalurl)
        elif method == "POST" or method == "PUT":
            if ("data" in case and "file" in case) and ("name" in case["file"] and "path" in case["file"]):
                data = case["data"]
                f = case["file"]
                if "fileType" in f:
                    fileType = f['fileType'] + "/*"
                else:
                    fileType = "*/*"
                try:
                    files = {
                        f["name"]: (
                            f["name"],
                            open(f["path"], "rb"),
                            fileType
                        )
                    }
                    if "headers" in case:
                        headers = case["headers"]
                        response = requests.post(
                            finalurl, data=data, files=files, headers=headers)
                    else:
                        response = requests.post(
                            finalurl, data=data, files=files)
                except Exception as error:
                    pass
            elif "data" in case and not "file" in case:
                data = case["data"]
                if "headers" in case:
                    headers = case["headers"]
                    response = requests.post(
                        finalurl, data=data, headers=headers)
                else:
                    response = requests.post(finalurl, data=data)
            elif (not "data" in case and "file" in case) and ("name" in case["file"] and "path" in case["file"]):
                f = case["file"]
                if "fileType" in f:
                    fileType = f['fileType'] + "/*"
                else:
                    fileType = "*/*"
                try:
                    files = {
                        f["name"]: (
                            f["name"],
                            open(f["path"], "rb"),
                            fileType
                        )
                    }
                    if "headers" in case:
                        headers = case["headers"]
                        response = requests.post(
                            finalurl, files=files, headers=headers)
                    else:
                        response = requests.post(finalurl, files=files)
                except Exception as error:
                    pass
        elif method == "HEAD":
            if "headers" in case:
                headers = case["headers"]
                response = requests.head(finalurl, headers=headers)
            else:
                response = requests.head(finalurl)
        elif method == "DELETE":
            if "headers" in case:
                headers = case["headers"]
                response = requests.delete(finalurl, headers=headers)
            else:
                response = requests.delete(finalurl)
    except Exception as error:
        print("Error: ", error)
    if DEBUG:
        print(f"{method} : {response}")


def startLoadTesting(testCases=[]):
    global CONFIG
    url = "http://localhost:" + str(CONFIG["DEFAULT"]["PORT"])
    threads = []
    wasteThread = 0
    start = time.time()
    try:
        for case in testCases:
            if "method" in case:
                method = case["method"].upper()
                if "url" in case:
                    finalurl = url + case["url"]
                else:
                    finalurl = url
                startThread = threading.Thread(
                    target=loadThreads, args=(case, method, finalurl, ))
                threads.append(startThread)
                startThread.start()
        for thread in threads:
            thread.join()
    except Exception as error:
        # print("Error: ", error)
        wasteThread += 1
    end = time.time()
    if len(threads) - wasteThread < 0:
        finalCount = 0
    else:
        finalCount = len(threads) - wasteThread
    print(f"Total requests : {finalCount}")
    print("Took {} seconds.".format(end - start))


def concurrentThreads(testCases=[]):
    global CONFIG
    url = "http://localhost:" + str(CONFIG["DEFAULT"]["PORT"])
    methods = []
    finalurls = []
    maxConnections = int(CONFIG["CONNECTIONS"]["Allowed"])
    for case in testCases:
        if "method" in case:
            methods.append(case["method"].upper())
        if "url" in case:
            finalurls.append(url + case["url"])
        else:
            finalurls.append(url)
    start = time.time()
    with ThreadPoolExecutor(max_workers=maxConnections) as pool:
        totalReqs = len(
            list(pool.map(loadThreads, testCases, methods, finalurls, )))
        print(f"Total requests : {totalReqs}")
    end = time.time()
    print("Took {} seconds.".format(end - start))


def readConfig():
    global CONFIG
    CONFIG = ConfigParser()
    try:
        if not os.path.isdir('ConfigFiles'):
            os.mkdir("ConfigFiles")
        CONFIG.read('ConfigFiles/config.ini')
    except Exception as error:
        sys.exit(1)


def runInstructions():
    print("Test:")
    print("\t1. Load:- \"python3 client_test.py -l <number-of-request>\"")
    print("\t2. Concurrent:- \"python3 client_test.py -c <number-of-request>\"")
    print("Options:")
    print("\t-l, --load : Perform load testing.")
    print("\t-c, --concurrent : Perform concurrent thread testing.")
    print("\t<number-of-request> : Integer value for multiple same requests present in Test.json file,\n\t\tDefault value: Number of request objest present in Test.json.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        readConfig()
        testCases = readTestFile("Test.json")
        if ("--load" in sys.argv and "--concurrent" in sys.argv) or ("-l" in sys.argv and "-c" in sys.argv) or ("-l" in sys.argv and "--concurrent" in sys.argv) or ("--load" in sys.argv and "-c" in sys.argv):
            runInstructions()
        elif "-l" in sys.argv or "--load" in sys.argv:
            reqNumber = 1
            try:
                intParams = [ele for ele in sys.argv if ele.isdigit()]
                if len(intParams) >= 1:
                    reqNumber = int(intParams[0])
            except Exception as error:
                print(
                    "Invalid number of requests number.\nStarted testing for default number.")
            if "--debug=True" in sys.argv:
                DEBUG = True
            startLoadTesting(testCases * reqNumber)
        elif "-c" in sys.argv or "--concurrent" in sys.argv:
            reqNumber = 1
            try:
                intParams = [ele for ele in sys.argv if ele.isdigit()]
                if len(intParams) >= 1:
                    reqNumber = int(intParams[0])
            except Exception as error:
                print(
                    "Invalid number of requests number.\nStarted testing for default number.")
            if "--debug=True" in sys.argv:
                DEBUG = True
            concurrentThreads(testCases * reqNumber)
    else:
        runInstructions()
