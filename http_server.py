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
        "php": "text/html",
        "pdf": "application/pdf",
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


def httpDateFormat(Ltime=False):
    return str(formatdate(timeval=None, localtime=Ltime, usegmt=True))


def isBadRequest(httpVersion, restHeaders):
    return httpVersion != "HTTP/1.1" or "Host" not in restHeaders

def writeErrorLog(Code="", Error=""):
    date = httpDateFormat(True)
    pid = str(os.getpid())
    tid = str(threading.current_thread().ident())
    log = "[" + date + "]" + " "
    log += "[core: " + Code + "]" + " "
    log += "[pid " + pid + ": " + "tid " + tid + "]" + " "
    log += str(Error) + "\n"
    try:
        with open("LogFiles/error.log", "a") as outputFile:
            outputFile.write(log)
    except Exception as e:
        with open("error.log", "a") as outputFile:
            outputFile.write(log)


def writeAccessLog(requestedMethod="", httpVersion="", requestedPath="", responseBodySize="-", restHeaders={}):
    global STATUSCODE
    date = httpDateFormat(True)
    log = "[" + date + "]" + " "
    log += "\"" + requestedMethod + " " + requestedPath + " " + httpVersion + "\"" + " "
    log += str(STATUSCODE) + " "
    log += str(responseBodySize) + " "
    if "Referer" in restHeaders:
        log += "\"" + restHeaders["Referer"].lstrip() + "\"" + " "
    if "User-Agent" in restHeaders:
        log += "\"" + restHeaders["User-Agent"].lstrip() + "\""
    log += "\n"
    try:
        with open("LogFiles/access.log", "a") as outputFile:
            outputFile.write(log)
    except Exception as error:
        writeErrorLog("error", error)


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
            except Exception as error:
                writeErrorLog("debug", error)
    return value


def getParsedData(connectionData=None):
    # print("CONNECTION DATA: ", connectionData)
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
        except Exception as error:
            writeErrorLog("debug", error)
            break
    if requestedMethod == "GET" or requestedMethod == "HEAD":
        pass
    elif requestedMethod == "POST":
        if "application/x-www-form-urlencoded" in restHeaders["Content-Type"]:
            tempBody = parsedData[headerEndCount + 1].split("&")
            for tbody in tempBody:
                try:
                    key, value = tbody.split("=")
                    requestBody[key] = parseRequestValueData(value)
                except Exception as error:
                    writeErrorLog("debug", error)
        elif "text/plain" in restHeaders["Content-Type"]:
            reqBody = parsedData[headerEndCount + 1:]
            for body in reqBody:
                try:
                    key, value = body.split("=")
                    requestBody[key] = value
                except Exception as error:
                    writeErrorLog("debug", error)
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
                    except Exception as error:
                        writeErrorLog("debug", error)
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
    except Exception as error:
        writeErrorLog("debug", error)
    try:
        requestedPath = getValidFilePath(requestedPath)
        requestedFile = open(requestedPath, fileMode)
    except Exception as error:
        writeErrorLog("debug", error)
    try:
        with requestedFile:
            finalFile = requestedFile.read()
    except Exception as error:
        writeErrorLog("error", error)
    return finalFile, fileExtension


def getBadRequestFile():
    global filePath
    finalFile = ""
    try:
        with open(filePath + "/bad_request.html", "r") as requestedFile:
            finalFile = requestedFile.read()
    except Exception as error:
        writeErrorLog("error", error)
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server - (400 - Bad  Request)</title></head><body><h1>400</h1><h2>Server received a Bad Request</h2></body></html>"
    return finalFile


def handleGETRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, filePath, Response
    finalFile = response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    if isBadRequest(httpVersion, restHeaders):
        STATUSCODE = 400
        httpVersion = "HTTP/1.1"
        finalFile = getBadRequestFile()
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
    responseBodySize = Response["Content-Length"]
    writeAccessLog("GET", httpVersion, requestedPath, responseBodySize, restHeaders)
    return response


def handlePOSTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, filePath
    finalFile = "<!DOCTYPE html><html><head><title>POST</title></head><body><h1>POST Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    if isBadRequest(httpVersion, restHeaders):
        STATUSCODE = 400
        httpVersion = "HTTP/1.1"
        finalFile = getBadRequestFile()
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n" + finalFile
        response = response.encode()
    else:
        STATUSCODE = 201
        if "filename" in requestBody:
            # tName = requestBody["filename"].split(".")
            resultFile = requestBody["filename"]
            # resultFile = ".".join(tName[0:-1]) + "(Server)." + tName[-1]
            with open("ClientFiles/" + resultFile, "a") as writeFile:
                writeFile.write(requestBody[requestBody["filename"]])
            del requestBody[requestBody["filename"]]
        newPostData = "POST Date: " + Response["Date"] + "\n" + "POST DATA:\n"
        for key, value in requestBody.items():
            newPostData += "\t" + str(key) + " = " + str(value) + "\n"
        newPostData += "\n" + "#"*60 + "\n\n"
        # Response["Content-Location"] = requestedPath
        with open(filePath + "/server_data.txt", "a") as outputFile:
            outputFile.write(newPostData)
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response += "\r\n" + finalFile
        response = response.encode()
    responseBodySize = Response["Content-Length"]
    writeAccessLog("POST", httpVersion, requestedPath, responseBodySize, restHeaders)
    return response


def handleHEADRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, filePath, Response
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    try:
        if os.path.isfile(filePath + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
    except Exception as error:
        writeErrorLog("debug", error)
    Response["Date"] = httpDateFormat()
    Response["Content-Type"] = switchContentType(fileExtension)
    STATUSCODE = 200
    if isBadRequest(httpVersion, restHeaders):
        STATUSCODE = 400
        httpVersion = "HTTP/1.1"
        finalFile = getBadRequestFile()
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = str(len(finalFile))
    elif requestedPath.endswith(tuple(imageFileExtensions)):
        path = getValidFilePath(requestedPath)
        if path.endswith(('not_found.html')):
            STATUSCODE = 404
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = str(os.path.getsize(path))
    else:
        path = getValidFilePath(requestedPath)
        if path.endswith(('not_found.html')):
            STATUSCODE = 404
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = str(os.path.getsize(path))
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n"
    response = response.encode()
    responseBodySize = Response["Content-Length"]
    writeAccessLog("HEAD", httpVersion, requestedPath, responseBodySize, restHeaders)
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
            elif requestedMethod == "HEAD":
                response = handleHEADRequest(httpVersion, restHeaders, requestedPath)
            clientConnection.send(response)
            # try:
            #     totalClientConnections.remove(clientConnection)
            #     clientConnection.close()
            # except:
            #     break

        except Exception as error:
            writeErrorLog("error", error)
            try:
                totalClientConnections.remove(clientConnection)
                clientConnection.close()
            except Exception as error:
                writeErrorLog("error", error)
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
