from socket import *
import threading
import sys
from email.utils import formatdate

totalClientConnections = []
filePath = "/home/viraj007/Semester 5/CN/Project/final/ResponseFiles/"
STATUSCODE = None
imageFileExtensions = [".png", ".jpeg", ".jpg",
                       ".ico", ".webp", ".apng", ".gif", ".bmp", ".svg"]


def switchStatusCode(code=None):
    codeTable = {
        200: " 200 OK",
        400: " 400 Bad Request",
        404: " 404 Not Found",
    }
    return codeTable.get(code, " 400 Bad Request")


def switchContentType(contentType=None):
    contentTable = {
        "txt": "text/plain",
        "html": "text/html",
        "csv": "text/csv",
        "apng": "image/apng",
        "bmp": "image/bmp",
        "gif": "image/gif",
        "ico": "image/x-icon",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "webp": "image/webp",
        "svg": "image/svg+xml",
        "json": "application/json",
        "js": "application/javascript"
    }
    return contentTable.get(contentType, "image/") + "; charset=utf-8"


def httpDateFormat():
    return str(formatdate(timeval=None, localtime=False, usegmt=True))


def getParsedData(connectionData=[]):
    parsedData = connectionData.split("\r\n")
    requestedMethod = None
    requestedPath = ""
    httpVersion = None
    restHeaders = dict()
    firstLine = parsedData[0].split()
    if len(firstLine) == 3:
        requestedMethod, requestedPath, httpVersion = firstLine
    elif len(firstLine) == 2:
        requestedMethod = firstLine[0]
        requestedPath = firstLine[1]
    elif len(firstLine) == 1:
        requestedMethod = firstLine[0]
    for data in parsedData[1:]:
        try:
            key, value = data.split(":", 1)
            restHeaders[key] = value
        except:
            pass
    return requestedMethod, requestedPath, httpVersion, restHeaders


def getValidFilePath(requestedPath=""):
    global filePath, STATUSCODE
    if requestedPath == None:
        STATUSCODE = 404
        return filePath + "not_found.html"
    # path = requestedPath.split("/")
    # if path[1] == '':
    #     return filePath + "index.html"
    # else:
    #     return filePath + "/".join(path[1:])
    if requestedPath == "/":
        return filePath + "index.html"
    else:
        return filePath + str(requestedPath[1:])


def getRequestedFile(requestedPath="", fileMode=""):
    global filePath, STATUSCODE
    finalFile = ""
    finalExtension = ""
    try:
        fileExtension = requestedPath.split(".")[-1]
        if fileExtension == "/":
            fileExtension = "html"
    except:
        pass
    try:
        requestedPath = getValidFilePath(requestedPath)
        requestedFile = open(requestedPath, fileMode)
    except:
        try:
            requestedFile = open(filePath + "not_found.html", "r")
            STATUSCODE = 404
            fileExtension = "html"
        except:
            pass
    with requestedFile:
        finalFile = requestedFile.read()
    return finalFile, fileExtension


def handleGETRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, filePath
    finalFile = response = ""
    fileExtension = "html"
    STATUSCODE = 200
    Response = {
        "Date": httpDateFormat(),
        "Server": "Delta-Server/0.0.1 (Ubuntu)",
        "Connection": "Close",
        # "Status": STATUSCODE str()
    }
    if httpVersion != "HTTP/1.1" or "Host" not in restHeaders:
        STATUSCODE = 400
        httpVersion = "HTTP/1.1"
        with open(filePath + "bad_request.html", "r") as requestedFile:
            finalFile = requestedFile.read()
        response = httpVersion + switchStatusCode(STATUSCODE) + "\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\n"
        response += "\n" + finalFile + "\n"
        response = response.encode()
    elif requestedPath.endswith((".html", "/", ".json", ".js")):
        finalFile, fileExtension = getRequestedFile(requestedPath, "r")
        response = httpVersion + switchStatusCode(STATUSCODE) + "\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\n"
        response += "\n" + finalFile + "\n"
        response = response.encode()
    elif requestedPath.endswith(tuple(imageFileExtensions)):
        finalFile, fileExtension = getRequestedFile(requestedPath, "rb")
        response = httpVersion + switchStatusCode(STATUSCODE) + "\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\n"
        response += "\n"
        response = response.encode() + finalFile
    else:
        STATUSCODE = 404
        with open(filePath + "not_found.html", "r") as requestedFile:
            finalFile = requestedFile.read()
        response = httpVersion + switchStatusCode(STATUSCODE) + "\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\n"
        response += "\n" + finalFile + "\n"
        response = response.encode()
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
            elif requestedMethod == "POST":
                pass
            elif requestedMethod == "PUT":
                pass
            elif requestedMethod == "DELETE":
                pass
            elif requestedMethod == "HEAD":
                pass
            clientConnection.send(response)
            # try:
            #     totalClientConnections.remove(clientConnection)
            #     clientConnection.close()
            # except:
            #     break

        except:
            try:
                totalClientConnections.remove(clientConnection)
                clientConnection.close()
            except:
                pass
            break


def startServer(serverSocket=None):
    while True:
        clientConnection, addr = serverSocket.accept()
        forEachConnection = threading.Thread(
            target=eachClientThread, args=(clientConnection, ))
        forEachConnection.start()


def establishConnection(argv=[]):
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverPort = int(argv[1])
    serverSocket.bind(('', serverPort))
    serverSocket.listen()
    return serverSocket


if __name__ == "__main__":
    serverSocket = establishConnection(sys.argv)
    print("The Server is ready to receive requests")
    startServer(serverSocket)
