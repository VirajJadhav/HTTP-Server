from socket import *
import threading
import sys
from email.utils import formatdate

totalClientConnections = []
filePath = "/home/viraj007/Semester 5/CN/Project/final/"
STATUSCODE = 400


def switchStatusCode(code=None):
    codeTable = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found",
    }
    return codeTable.get(code, "Bad Request")


def httpDateFormat():
    return formatdate(timeval=None, localtime=False, usegmt=True)


def getValidFilePath(requestedPath=None):
    if requestedPath == None:
        return "not_found.html"
    path = requestedPath.split("/")
    if path[1] == '':
        return "index.html"
    else:
        return path[1:].join("/")


def getParsedData(connectionData=None):
    parsedData = connectionData.split("\r\n")
    requestedMethod = requestedPath = httpVersion = restHeaders = None
    firstLine = parsedData[0].split()
    if len(firstLine) == 3:
        requestedMethod, requestedPath, httpVersion = firstLine
    elif len(firstLine) == 2:
        requestedMethod = firstLine[0]
        requestedPath = firstLine[1]
    elif len(firstLine) == 1:
        requestedMethod = firstLine[0]
    restHeaders = dict()
    for data in parsedData[1:]:
        try:
            key, value = data.split(":", 1)
            restHeaders[key] = value
        except:
            pass
    return requestedMethod, requestedPath, httpVersion, restHeaders


def handleGETRequest(httpVersion=None, restHeaders=None, requestedPath=None):
    global STATUSCODE
    response = httpVersion + " " + STATUSCODE + \
        " " + switchStatusCode(STATUSCODE) + "\n"
    response += "Date: " + httpDateFormat() + "\n"
    response += "Server: Delta/0.0.1 (Ubuntu)\n"
    if restHeaders != None:
        response += "Connection:" + \
            restHeaders["Connection"] + "\n"
    else:
        "Connection: close\n"
    response += "Content-Type: text/html; charset=iso-8859-1\n\n"
    try:
        requestedPath = getValidFilePath(requestedPath)
        requestedFile = open(requestedPath, "r")
    except:
        try:
            requestedFile = open("not_found.html", "r")
        except:
            pass
    with requestedFile:
        response += requestedFile.read() + "\n"
    return response


def eachClientThread(clientConnection=None):
    global totalClientConnections
    totalClientConnections.append(clientConnection)
    while True:
        try:
            connectionData = clientConnection.recv(1024).decode('utf-8')
            requestedMethod, requestedPath, httpVersion, restHeaders = getParsedData(
                connectionData)
            if requestedMethod == "GET":
                response = handleGETRequest(
                    httpVersion, restHeaders, requestedPath)
            clientConnection.send(response.encode())

        except:
            # index = totalClientConnections.index(clientConnection)
            # print("This is the index ", index)
            totalClientConnections.remove(clientConnection)
            clientConnection.close()
            break


def startServer(serverSocket=None):
    while True:
        clientConnection, addr = serverSocket.accept()
        # print("New request from ", addr)
        # print("Connection socket is ", connectionSocket)
        forEachConnection = threading.Thread(
            target=eachClientThread, args=(clientConnection, ))
        forEachConnection.start()
    # serverSocket.close()


def establishConnection(argv=None):
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverPort = int(argv[1])
    serverSocket.bind(('', serverPort))
    serverSocket.listen()
    return serverSocket


if __name__ == "__main__":
    serverSocket = establishConnection(sys.argv)
    print("The Server is ready to receive")
    startServer(serverSocket)
