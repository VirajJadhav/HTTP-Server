import requests
import json
from configparser import ConfigParser
import sys
import os
import threading
import time
# from concurrent.futures import ThreadPoolExecutor

# store config data
CONFIG = None

# store and check debug value
DEBUG = False

WASTETHREAD = 0

# read config file


def readTestFile(fileName=""):
    testCases = []
    if not os.path.isfile(fileName):
        with open(fileName, "w") as f:
            json.dump([], f, indent=4)
    with open(fileName, "r") as f:
        testCases = json.load(f)
    return testCases


# function for load testing for each case
def loadThreads(case={}, method="", finalurl=""):
    global DEBUG, WASTETHREAD
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
        # print("Error: ", error)
        WASTETHREAD += 1
    if DEBUG:
        print(f"{method} : {response}")

# function to start load testing for all cases


def startLoadTesting(testCases=[]):
    global CONFIG, WASTETHREAD
    url = "http://localhost:" + str(CONFIG["DEFAULT"]["PORT"])
    threads = []
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
        print("Error: ", error)
    end = time.time()
    if len(threads) - WASTETHREAD < 0:
        finalCount = 0
    else:
        finalCount = len(threads) - WASTETHREAD
    print(f"Total requests : {finalCount}")
    print("Took {} seconds.".format(end - start))

# Concurrent Testing using concurrent.futures module
# def concurrentThreads(testCases=[]):
#     global CONFIG
#     url = "http://localhost:" + str(CONFIG["DEFAULT"]["PORT"])
#     methods = []
#     finalurls = []
#     maxConnections = int(CONFIG["CONNECTIONS"]["Allowed"])
#     for case in testCases:
#         if "method" in case:
#             methods.append(case["method"].upper())
#         if "url" in case:
#             finalurls.append(url + case["url"])
#         else:
#             finalurls.append(url)
#     start = time.time()
#     with ThreadPoolExecutor(max_workers=maxConnections) as pool:
#         totalReqs = len(
#             list(pool.map(loadThreads, testCases, methods, finalurls, )))
#         print(f"Total requests : {totalReqs}")
#     end = time.time()
#     print("Took {} seconds.".format(end - start))


# function to execute one request at a time for confimation testing
def confirmationTesting(testCases=[], method=""):
    global CONFIG
    url = "http://localhost:" + str(CONFIG["DEFAULT"]["PORT"])
    flag = False
    for case in testCases:
        if "method" in case and case["method"] == method:
            if "url" in case:
                finalurl = url + case["url"]
            else:
                finalurl = url
            loadThreads(case, method, finalurl)
            flag = True
            break
    if not flag:
        print("Method not present in CTest.json file.\nPlease update request method packet accordingly in CTest.json")


def readConfig():
    global CONFIG
    CONFIG = ConfigParser()
    try:
        if not os.path.isdir('ConfigFiles'):
            os.mkdir("ConfigFiles")
        CONFIG.read('ConfigFiles/config.ini')
    except Exception as error:
        sys.exit(1)

# default runnning instructions


def runInstructions():
    print("Test:")
    print("\t1. Load:- \"python3 client_test.py -l <number-of-request>\"")
    print("\t2. Confirmation:- \"python3 client_test.py -c <method-name>\"")
    print("Options:")
    print("\t-l, --load : Perform load testing.")
    print("\t-c, --confirmation : Perform confirmation testing.")
    print("\t<number-of-request> (optional) : Integer value for multiple same requests present in LTest.json file,\n\t\tDefault value: Number of request objest present in LTest.json.")
    print("\t<method-name> : GET | POST | PUT | DELETE | HEAD (requests present in CTest.json file)")
    print("\t--debug=True : For logging response codes on terminal for respective request methods.")
    print("\nPlease read README.md for detailed information.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and len(sys.argv) < 5:
        readConfig()
        if ("--load" in sys.argv and "--confirmation" in sys.argv) or ("-l" in sys.argv and "-c" in sys.argv) or ("-l" in sys.argv and "--confirmation" in sys.argv) or ("--load" in sys.argv and "-c" in sys.argv):
            runInstructions()
        elif "-l" in sys.argv or "--load" in sys.argv:
            testCases = readTestFile("LTest.json")
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
        elif "-c" in sys.argv or "--confirmation" in sys.argv:
            testCases = readTestFile("CTest.json")
            validInputMethods = ["GET", "POST", "PUT", "DELETE", "HEAD"]
            if "--debug=True" in sys.argv:
                DEBUG = True
            try:
                methodParams = [
                    ele for ele in sys.argv if ele in validInputMethods]
                if len(methodParams) >= 1:
                    confirmationTesting(testCases, methodParams[0].upper())
                else:
                    print("Invalid request method.\n")
                    runInstructions()
            except Exception as error:
                print("Invalid request method.\n")
                runInstructions()
        else:
            runInstructions()
    else:
        runInstructions()
