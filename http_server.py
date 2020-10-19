from socket import *
import threading
import sys
from email.utils import formatdate
import os

totalClientConnections = []
# filePath = "/home/viraj007/Semester 5/CN/Project/final/ResponseFiles/"
filePath = "ResponseFiles"
STATUSCODE = None
imageFileExtensions = [".png", ".jpeg", ".jpg",
                       ".ico", ".webp", ".apng", ".gif", ".bmp", ".svg"]
Response = {
    "Date": "",
    "Server": "Delta-Server/0.0.1 (Ubuntu)",
    "Connection": "Close",
    # "Status": STATUSCODE str()
}


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


def getParsedData(connectionData=None):
    parsedData = connectionData.split("\r\n")
    headerEndCount = 0
    requestedMethod = None
    requestedPath = ""
    httpVersion = None
    requestBody = {}
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
        headerEndCount += 1
        try:
            key, value = data.split(":", 1)
            restHeaders[key] = value
        except:
            break
    if requestedMethod == "GET":
        pass
    elif requestedMethod == "POST":
        if "application/x-www-form-urlencoded" in restHeaders["Content-Type"]:
            tempBody = parsedData[headerEndCount + 1].split("&")
            for tbody in tempBody:
                try:
                    key, value = tbody.split("=")
                    tvalue = value.split("%")
                    value = tvalue[0]
                    if len(tvalue) > 1:
                        for i in range(1, len(tvalue)):
                            try:
                                bytesData = bytes.fromhex(
                                    tvalue[i][:2])
                                value += bytesData.decode("ASCII") + \
                                    tvalue[i][2:]
                            except:
                                pass
                    requestBody[key] = value
                except:
                    pass
        elif "multipart/form-data" in restHeaders["Content-Type"]:
            # reqBoundary = restHeaders["Content-Type"].split("boundary=")[1]
            reqBody = parsedData[headerEndCount + 1:]
            for i in range(1, len(reqBody) - 4, 4):
                tkey = reqBody[i].split(";")[1].split("name=")[1].strip("\"")
                requestBody[tkey] = reqBody[i + 2]
    return requestedMethod, requestedPath, httpVersion, restHeaders, requestBody


def getValidFilePath(requestedPath=""):
    global filePath, STATUSCODE
    requestedPath = str(requestedPath)
    if os.path.isdir(filePath + requestedPath):
        if requestedPath.endswith(('/')):
            return filePath + requestedPath + "index.html"
        else:
            return filePath + requestedPath + "/index.html"
    elif os.path.isfile(filePath + requestedPath):
        return filePath + requestedPath
    else:
        STATUSCODE = 404
        return filePath + "/not_found.html"


def getRequestedFile(requestedPath="", fileMode=""):
    global filePath, STATUSCODE
    finalFile = ""
    finalExtension = ""
    try:
        if os.path.isfile(filePath + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
        else:
            fileExtension = "html"
    except:
        pass
    try:
        requestedPath = getValidFilePath(requestedPath)
        requestedFile = open(requestedPath, fileMode)
    except:
        pass
    with requestedFile:
        finalFile = requestedFile.read()
    return finalFile, fileExtension


def handleGETRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, filePath, Response
    finalFile = response = ""
    fileExtension = "html"
    STATUSCODE = 200
    Response["Date"] = httpDateFormat()
    if httpVersion != "HTTP/1.1" or "Host" not in restHeaders:
        STATUSCODE = 400
        httpVersion = "HTTP/1.1"
        with open(filePath + "/bad_request.html", "r") as requestedFile:
            finalFile = requestedFile.read()
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n" + finalFile
        response = response.encode()
    elif requestedPath.endswith(tuple(imageFileExtensions)):
        finalFile, fileExtension = getRequestedFile(requestedPath, "rb")
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n"
        response = response.encode() + finalFile
    else:
        finalFile, fileExtension = getRequestedFile(requestedPath, "r")
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n" + finalFile
        response = response.encode()
    return response


def handlePOSTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response
    Response["Date"] = httpDateFormat()
    pass


def eachClientThread(clientConnection=None):
    global totalClientConnections
    totalClientConnections.append(clientConnection)
    while True:
        try:
            connectionData = clientConnection.recv(1024).decode('utf-8')
            requestedMethod, requestedPath, httpVersion, restHeaders, requestBody = getParsedData(
                connectionData)
            response = b'HTTP/1.1 200 OK\r\n'
            if requestedMethod == "GET":
                response = handleGETRequest(
                    httpVersion, restHeaders, requestedPath)
            elif requestedMethod == "POST":
                response = handlePOSTRequest(
                    httpVersion, restHeaders, requestedPath, requestBody)
            # elif requestedMethod == "PUT":
            #     pass
            # elif requestedMethod == "DELETE":
            #     pass
            # elif requestedMethod == "HEAD":
            #     pass
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
