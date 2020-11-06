from socket import *
import threading
import sys
from configparser import ConfigParser


CONFIG = None


def listenServer(clientSocket=None):
    # while True:
    try:
        response = clientSocket.recv(1024)
        print(response.decode('ISO-8859-1'))
        # clientSocket.close()
        # break
    except Exception as error:
        print(error)
        pass


def startClient(clientSocket=None, testCases=None):
    for case in testCases:
        validCase = case.strip("\n")
        print(validCase)
        validCase = "\r\n".join(case.split("\n"))
        # print(validCase.encode('ISO-8859-1'))
        try:
            clientSocket.send(validCase.encode('ISO-8859-1'))
            # break
        except Exception as error:
            print(error)
        # break


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
    return testCases


if __name__ == "__main__":
    readConfig()
    testCases = readTestFile()
    clientSocket = establishConnection()
    keepListening = threading.Thread(
        target=listenServer, args=(clientSocket, ))
    keepListening.start()
    startRequest = threading.Thread(
        target=startClient, args=(clientSocket, testCases, ))
    startRequest.start()
