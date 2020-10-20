from socket import *
import threading
import sys
from email.utils import formatdate
import os
import json

# default port
PORT = 4000
totalClientConnections = []
# filePath = "/home/viraj007/Semester 5/CN/Project/final/ResponseFiles/"
filePath = "ResponseFiles"
STATUSCODE = None
imageFileExtensions = [".png", ".jpeg", ".jpg",
                       ".ico", ".webp", ".apng", ".gif", ".bmp", ".svg"]
Response = {
    "Date": "",
    "Server": "Delta-Server/0.0.1 (Ubuntu)",
    "Connection": "close",
    # "Status": STATUSCODE str()
}


def switchStatusCode(code=None):
    codeTable = {
        200: " 200 OK",
        201: " 201 Created",
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


def isBadRequest(httpVersion, restHeaders):
    return httpVersion != "HTTP/1.1" or "Host" not in restHeaders


def parseRequestValueData(value=None):
    tvalue = value.split("%")
    if "+" in tvalue[0]:
        value = tvalue[0].replace("+", " ")
    else:
        value = tvalue[0]
    if len(tvalue) > 1:
        for i in range(len(tvalue)):
            if "+" in tvalue[i]:
                value += tvalue[i].replace("+", " ")
            try:
                bytesData = bytes.fromhex(
                    tvalue[i][:2])
                value += bytesData.decode("ASCII") + \
                    tvalue[i][2:]
            except:
                pass
    return value


def getParsedData(connectionData=None):
    # print("CONNECTION DATA: ", connectionData)
    parsedData = connectionData.split("\r\n")
    # print(parsedData)
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
    elif requestedMethod == "POST" and requestedPath.endswith(('book')):
        if "application/x-www-form-urlencoded" in restHeaders["Content-Type"]:
            tempBody = parsedData[headerEndCount + 1].split("&")
            for tbody in tempBody:
                try:
                    key, value = tbody.split("=")
                    requestBody[key] = parseRequestValueData(value)
                except:
                    pass
        elif "text/plain" in restHeaders["Content-Type"]:
            reqBody = parsedData[headerEndCount + 1:]
            for body in reqBody:
                try:
                    key, value = body.split("=")
                    requestBody[key] = value
                except:
                    pass
        elif "multipart/form-data" in restHeaders["Content-Type"]:
            # reqBoundary = restHeaders["Content-Type"].split("boundary=")[1]
            reqBody = parsedData[headerEndCount + 1:]
            for i in range(1, len(reqBody) - 4):
                if ";" in reqBody[i]:
                    try:
                        tbody = reqBody[i].split(";")
                        if len(tbody) == 2:
                            tkey = tbody[1].split("name=")[
                                1].strip("\"")
                            requestBody[tkey] = reqBody[i + 2]
                        elif len(tbody) == 3:
                            tkey = tbody[2].split("filename=")[1].strip("\"")
                            requestBody[tkey] = str(reqBody[i + 3])
                            requestBody["filename"] = tkey
                    except:
                        pass
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
    Response["Date"] = httpDateFormat()
    splitReqPath = requestedPath.split("?")
    if isBadRequest(httpVersion, restHeaders):
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
        STATUSCODE = 200
        finalFile, fileExtension = getRequestedFile(requestedPath, "rb")
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        # Response["Status"] = STATUSCODE
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n"
        response = response.encode() + finalFile
    elif len(splitReqPath) <= 2 and splitReqPath[0].endswith(("book")):
        params = ""
        try:
            params = splitReqPath[1].split("&")
        except:
            pass
        query = {}
        requestedData = {}
        if len(params) <= 2 and len(params) > 0:
            for p in params:
                try:
                    key, value = p.split("=")
                    query[key] = parseRequestValueData(value)
                except:
                    pass
            with open(filePath + "/server_data.json") as dataFile:
                jsonDataFile = json.load(dataFile)
            for data in jsonDataFile:
                try:
                    if "bookID" in query and "name" not in query and data["bookID"] == int(query["bookID"]):
                        requestedData = dict(data)
                        break
                    elif "name" in query and "bookID" not in query and data["name"] == query["name"]:
                        requestedData = dict(data)
                        break
                    elif "bookID" in query and "name" in query and data["name"] == query["name"] and data["bookID"] == int(query["bookID"]):
                        requestedData = dict(data)
                        break
                except:
                    pass
        elif len(params) == 0:
            with open(filePath + "/server_data.json") as dataFile:
                jsonDataFile = json.load(dataFile)
                requestedData = jsonDataFile
        if not requestedData:
            STATUSCODE = 404
            with open(filePath + "/not_found.html", "r") as outputFile:
                finalFile = outputFile.read()
                Response["Content-Length"] = str(len(finalFile))
                Response["Content-Type"] = switchContentType("html")
        else:
            STATUSCODE = 200
            Response["Content-Length"] = str(len(str(requestedData)))
            Response["Content-Type"] = switchContentType("json")
            finalFile = json.dumps(requestedData)
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n" + finalFile
        response = response.encode()
    else:
        STATUSCODE = 200
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
    global Response, STATUSCODE, filePath
    finalFile = "<html><head><title>POST</title></head><body><h1>POST Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    Response["Date"] = httpDateFormat()
    if not requestedPath.endswith(('book')) or isBadRequest(httpVersion, restHeaders):
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
    elif requestedPath.endswith(('book')):
        STATUSCODE = 200
        jsonDataFile = []
        flag = False
        bookID = None
        if "filename" in requestBody:
            STATUSCODE = 201
            tName = requestBody["filename"].split(".")
            resultFile = ".".join(tName[0:-1]) + "(Server)." + tName[-1]
            with open("ClientFiles/" + resultFile, "a") as writeFile:
                writeFile.write(requestBody[requestBody["filename"]])
        else:
            with open(filePath + "/server_data.json") as dataFile:
                jsonDataFile = json.load(dataFile)
            for data in jsonDataFile:
                if data["name"] == requestBody["name"]:
                    flag = True
                    bookID = data["bookID"]
                    break
            if not flag:
                STATUSCODE = 201
                requestBody["bookID"] = len(jsonDataFile) + 1
                Response["Content-Location"] = "/book/" + \
                    str(requestBody["bookID"])
                jsonDataFile.append(requestBody)
                jsonObject = json.dumps(jsonDataFile, indent=4)
                with open(filePath + "/server_data.json", "w") as outputFile:
                    outputFile.write(jsonObject)
            else:
                Response["Content-Location"] = "/book/" + \
                    str(bookID)
                finalFile = "<html><head><title>POST</title></head><body><h1>Data already present</h1></body></html>"
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n" + finalFile
        response = response.encode()
    return response


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
    global PORT
    serverSocket = socket(AF_INET, SOCK_STREAM)
    try:
        serverPort = int(argv[1])
    except:
        serverPort = PORT
    serverSocket.bind(('', serverPort))
    serverSocket.listen()
    return serverSocket


if __name__ == "__main__":
    serverSocket = establishConnection(sys.argv)
    print("The Server is ready to receive requests")
    startServer(serverSocket)
