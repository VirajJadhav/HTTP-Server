from socket import *
import threading
import sys
import time
from configparser import ConfigParser


CONFIG = None


def establishConnection():
    global CONFIG
    clientSocket = socket(AF_INET, SOCK_STREAM)
    try:
        serverPort = int(CONFIG.get("DEFAULT", "PORT"))
    except Exception as error:
        print(error, 'of config file.')
        print("Please specify a valid listen port in default section of config file.")
        sys.exit(1)
    try:
        # clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        clientSocket.connect(('', serverPort))
    except Exception as error:
        print(error)
        sys.exit(1)
    return clientSocket


def readConfig():
    global CONFIG
    CONFIG = ConfigParser()
    try:
        CONFIG.read('ConfigFiles/config.ini')
    except Exception as error:
        pass


def readTestFile():
    testCases = []
    testFile = ""
    with open("test.txt", "r") as testFile:
        testFile = testFile.read()
    testCases = testFile.split("#" * 30)
    return testCases * 500


def listenServer(clientSocket=None):
    try:
        response = clientSocket.recv(1024).decode('ISO-8859-1')
        # print(response)
        # print("#"*30)
        # clientSocket.close()
        # break
    except Exception as error:
        print(error)
        pass


def startClient(clientSocket=None, case=None):
    validCase = case.lstrip("\n")
    validCase = "\r\n".join(validCase.split("\n"))
    try:
        clientSocket.send(validCase.encode('ISO-8859-1'))
        # break
    except Exception as error:
        print(error)
        # break


def startTesting(testCases=[]):
    for case in testCases:
        if case == '':
            continue
        clientSocket = establishConnection()
        keepListening = threading.Thread(
            target=listenServer, args=(clientSocket, ))
        keepListening.start()
        startRequest = threading.Thread(
            target=startClient, args=(clientSocket, case, ))
        startRequest.start()
        # clientSocket.close()


if __name__ == "__main__":
    readConfig()
    testCases = readTestFile()
    start = time.time()
    startTesting(testCases)
    end = time.time()
    print(f"Took {end - start} seconds")
