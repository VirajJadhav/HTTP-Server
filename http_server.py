from socket import *
import threading
from datetime import datetime, timezone
from email.utils import formatdate
import sys
import os
from configparser import ConfigParser
from shutil import rmtree
from uuid import uuid4
import json


CONFIG = None

CLIENTIP = None

STATUSCODE = None

imageFileExtensions = [".png", ".jpeg", ".jpg",
                       ".ico", ".webp", ".apng", ".gif", ".bmp", ".svg"]
Response = {
    "Date": "",
    "Server": "Delta-Server/0.0.1 (Ubuntu)",
    "Connection": "close",
    "Content-Language": "en-US",
}


def switchStatusCode(code=None):
    codeTable = {
        200: " 200 OK",
        201: " 201 Created",
        304: " 304 Not Modified",
        400: " 400 Bad Request",
        403: " 403 Forbidden",
        404: " 404 Not Found",
        411: " 411 Length Required",
        415: " 415 Unsupported Media Type",
        501: " 501 Not Implemented",
        505: " 505 HTTP Version Not Supported",
    }
    return codeTable.get(code, " 400 Bad Request")


def switchContentType(contentType=None):
    contentTable = {
        "txt": "text/plain",
        "html": "text/html",
        "php": "text/html",
        "pdf": "application/pdf",
        "css": "text/css",
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
        "js": "application/javascript",
        "bin": "application/octet-stream",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "mpeg": "video/mpeg",
        "webm": "video/webm",
        "3gp": "video/3gpp"
    }
    return contentTable.get(contentType, "text/plain") + "; charset=ISO-8859-1"


def httpDateFormat(Ltime=False):
    return str(formatdate(timeval=None, localtime=Ltime, usegmt=True))


def getLastModifiedTime(path=""):
    lastModified = ""
    try:
        msecs = os.path.getmtime(path)
    except Exception as error:
        msecs = 0
        # writeErrorLog("error", error)
    lastModified = datetime.fromtimestamp(
        msecs, timezone.utc).strftime("%a, %d %b %Y %H:%M:%S") + " GMT"
    return lastModified


def writeErrorLog(Code="", Error=""):
    global CLIENTIP, CONFIG
    date = httpDateFormat(True)
    pid = str(os.getpid())
    tid = str(threading.current_thread().ident)
    log = "[" + date + "]" + " "
    log += "[core: " + Code + "]" + " "
    log += "[pid " + pid + ":tid " + tid + "]" + " "
    if CLIENTIP != None:
        log += "[client " + CLIENTIP + "]" + " "
    log += str(Error) + "\n"
    try:
        if not os.path.isdir(CONFIG['LOG']['Directory']):
            os.mkdir(CONFIG['LOG']['Directory'])
        with open(CONFIG['LOG']['Error'], "a") as outputFile:
            outputFile.write(log)
    except Exception as e:
        with open("error.log", "a") as outputFile:
            outputFile.write(log)


def writeAccessLog(requestedMethod="", httpVersion="", requestedPath="", responseBodySize="-", restHeaders={}):
    global STATUSCODE, CLIENTIP, CONFIG
    date = httpDateFormat(True)
    if CLIENTIP != None:
        log = CLIENTIP + " "
    else:
        log = "- "
    log += "[" + date + "]" + " "
    log += "\"" + requestedMethod + " " + \
        requestedPath + " " + httpVersion + "\"" + " "
    log += str(STATUSCODE) + " "
    log += str(responseBodySize) + " "
    if "Referer" in restHeaders:
        log += "\"" + restHeaders["Referer"].lstrip() + "\"" + " "
    else:
        log += "\"-\"" + " "
    if "User-Agent" in restHeaders:
        log += "\"" + restHeaders["User-Agent"].lstrip() + "\""
    else:
        log += "\"-\"" + " "
    log += "\n"
    try:
        if not os.path.isdir(CONFIG['LOG']['Directory']):
            os.mkdir(CONFIG['LOG']['Directory'])
        with open(CONFIG['LOG']['Access'], "a") as outputFile:
            outputFile.write(log)
    except Exception as error:
        # writeErrorLog("error", error)
        pass


def validateRequest(requestedMethod="", httpVersion="", restHeaders={}):
    global STATUSCODE, Response
    finalFile = ""
    response = ""
    fileExtension = "html"
    Response["Date"] = httpDateFormat()
    # if requestedMethod == None:
    #     return response, False
    if requestedMethod not in ["GET", "POST", "PUT", "DELETE", "HEAD"]:
        STATUSCODE = 501
        httpVersion = "HTTP/1.1"
        response = httpVersion + \
            switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Length"] = "0"
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        response = response.encode('ISO-8859-1')
        return response, Response["Content-Length"], False
    elif httpVersion != "HTTP/1.1":
        STATUSCODE = 505
        response = "HTTP/1.1" + switchStatusCode(STATUSCODE) + "\r\n"
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>505</h1><h2>HTTP Version Not Supported</h2></body></html>"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        if requestedMethod != "HEAD":
            response += "\r\n" + finalFile
        response = response.encode('ISO-8859-1')
        return response, Response["Content-Length"], False
    elif ("Host" not in restHeaders) or (requestedMethod in ["POST", "PUT"] and "Content-Type" not in restHeaders):
        STATUSCODE = 400
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>400</h1><h2>Server received a Bad Request</h2></body></html>"
        response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
        Response["Content-Type"] = switchContentType(fileExtension)
        Response["Content-Length"] = str(len(finalFile))
        for key, value in Response.items():
            response += key + ": " + value + "\r\n"
        if requestedMethod != "HEAD":
            response += "\r\n" + finalFile
        response = response.encode('ISO-8859-1')
        return response, Response["Content-Length"], False
    elif requestedMethod in ["POST", "PUT"]:
        if "Content-Length" not in restHeaders:
            STATUSCODE = 411
            finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>411</h1><h2>Server received a request without Content Length</h2></body></html>"
            response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
            Response["Content-Type"] = switchContentType(fileExtension)
            Response["Content-Length"] = str(len(finalFile))
            for key, value in Response.items():
                response += key + ": " + value + "\r\n"
            response += "\r\n" + finalFile
            response = response.encode('ISO-8859-1')
            return response, Response["Content-Length"], False
        elif "Content-Type" in restHeaders:
            actualType = restHeaders["Content-Type"].strip().split(";")[0]
            if actualType not in ["application/x-www-form-urlencoded", "text/plain", "multipart/form-data"]:
                STATUSCODE = 415
                finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>415</h1><h2>Server received a request with unsupported media type</h2></body></html>"
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                Response["Content-Type"] = switchContentType(fileExtension)
                Response["Content-Length"] = str(len(finalFile))
                for key, value in Response.items():
                    response += key + ": " + value + "\r\n"
                response += "\r\n" + finalFile
                response = response.encode('ISO-8859-1')
                return response, Response["Content-Length"], False
    return response, 0, True


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
                value += bytesData.decode("ASCII") + tvalue[i][2:]
            except Exception as error:
                # writeErrorLog("debug", error)
                pass
    return value


def getParsedData(connectionData=None, clientConnection=None):
    global imageFileExtensions
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
        except Exception as error:
            # writeErrorLog("debug", error)
            break
    if requestedMethod == "GET" or requestedMethod == "HEAD":
        pass
    elif requestedMethod == "POST" or requestedMethod == "PUT":
        actualLength = int(restHeaders["Content-Length"].strip())
        receivedBody = connectionData.split("\r\n\r\n")[1:]
        lengthReceivedBody = int(len("\r\n\r\n".join(receivedBody)))
        if actualLength > 1024 or (actualLength - lengthReceivedBody) > 0:
            extraData = actualLength - lengthReceivedBody
            # extraData = abs(actualLength - int(len(connectionData)))
            try:
                while extraData > 0:
                    extraConnectionData = clientConnection.recv(
                        1024).decode('ISO-8859-1')
                    connectionData = str(connectionData) + \
                        str(extraConnectionData)
                    extraData -= int(len(extraConnectionData))
            except Exception as error:
                # writeErrorLog("debug", error)
                pass
            parsedData = list(connectionData.split("\r\n"))
        if "Content-Type" in restHeaders:
            if "application/x-www-form-urlencoded" in restHeaders["Content-Type"]:
                tempBody = parsedData[headerEndCount + 1].split("&")
                for tbody in tempBody:
                    try:
                        key, value = tbody.split("=")
                        requestBody[key] = parseRequestValueData(value)
                    except Exception as error:
                        # writeErrorLog("debug", error)
                        pass
            elif "text/plain" in restHeaders["Content-Type"]:
                reqBody = parsedData[headerEndCount + 1:]
                for body in reqBody:
                    try:
                        key, value = body.split("=")
                        requestBody[key] = value
                    except Exception as error:
                        # writeErrorLog("debug", error)
                        pass
            elif "multipart/form-data" in restHeaders["Content-Type"]:
                # reqBoundary = restHeaders["Content-Type"].split("boundary=")[1]
                reqBody = parsedData[headerEndCount + 1:]
                for i in range(1, len(reqBody) - 4):
                    if ";" in reqBody[i]:
                        try:
                            tbody = reqBody[i].split(";")
                            if len(tbody) == 2:
                                tkey = tbody[1].split("name=")[1].strip("\"")
                                requestBody[tkey] = reqBody[i + 2]
                            elif len(tbody) == 3:
                                tkey = tbody[2].split("filename=")[
                                    1].strip("\"")
                                requestBody[tkey] = str(reqBody[i + 3])
                                if str(tkey).endswith(tuple(imageFileExtensions)):
                                    requestBody[tkey] += "\r\n" + \
                                        str(reqBody[i + 4])
                                requestBody["filename"] = tkey
                        except Exception as error:
                            # writeErrorLog("debug", error)
                            pass
    return requestedMethod, requestedPath, httpVersion, restHeaders, requestBody


def getValidFilePath(requestedPath=""):
    global STATUSCODE, CONFIG
    requestedPath = str(requestedPath)
    if 'DocumentRoot' not in CONFIG['PATH']:
        # Need to modify later
        STATUSCODE = 404
        return 'ResponseFiles/not_found.html'
    else:
        if os.path.isdir(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            if requestedPath.endswith(('/')):
                return CONFIG['PATH']['DocumentRoot'] + requestedPath + "index.html"
            else:
                return CONFIG['PATH']['DocumentRoot'] + requestedPath + "/index.html"
        elif os.path.isfile(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            return CONFIG['PATH']['DocumentRoot'] + requestedPath
        else:
            STATUSCODE = 404
            return CONFIG['PATH']['DocumentRoot'] + "/not_found.html"


def getRequestedFile(requestedPath="", fileMode=""):
    global STATUSCODE, CONFIG
    finalExtension = ""
    try:
        if os.path.isfile(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
        else:
            fileExtension = "html"
    except Exception as error:
        # writeErrorLog("debug", error)
        pass
    try:
        newRequestedPath = getValidFilePath(requestedPath)
    except Exception as error:
        # writeErrorLog("debug", error)
        pass
    lastModified = getLastModifiedTime(newRequestedPath)
    # print("FILE REPRESENTATIONS BEFORE RETURNING: ",
    #       newRequestedPath, fileExtension, lastModified)
    return newRequestedPath, fileExtension, lastModified


def setCookie(clientIP=None, restHeaders={}):
    global CONFIG
    # if "Cookie" in restHeaders:
    #     return restHeaders["Cookie"].lstrip() + "; SameSite=Strict"
    # else:
    cookieFile = CONFIG['COOKIE']['File']
    if not os.path.isfile(cookieFile):
        with open(cookieFile, "w") as f:
            json.dump([], f, indent=4)
    try:
        cookieData = []
        with open(cookieFile) as searchFile:
            cookieData = json.load(searchFile)
        for cookie in cookieData:
            if cookie["clientIP"] == str(clientIP) and "cookie" in cookie:
                return "name=" + cookie['cookie'] + "; SameSite=Strict"
        newCookie = uuid4()
        newClient = {
            'clientIP': str(clientIP),
            'cookie': str(newCookie)
        }
        cookieData.append(newClient)
        with open(cookieFile, "w") as searchFile:
            json.dump(cookieData, searchFile, indent=4)
        return "name=" + newClient['cookie'] + "; SameSite=Strict"
    except Exception as error:
        # writeErrorLog("debug", error)
        pass


def getForbiddenResponse(httpVersion="", restHeaders={}):
    global STATUSCODE, CLIENTIP
    STATUSCODE = 403
    fileExtension = "html"
    finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>403</h1><h2>Server refuses to process request (restricted resource access)</h2></body></html>"
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += str(key) + ": " + str(value) + "\r\n"
    response += "\r\n" + finalFile
    return response, Response["Content-Length"]


def handleGETRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, Response, CLIENTIP
    finalFile = response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 200
    # print("REST HEADERS: ", restHeaders)
    if requestedPath.endswith(tuple(imageFileExtensions)):
        newRequestedPath, fileExtension, lastModified = getRequestedFile(
            requestedPath, "rb")
        if not os.access(newRequestedPath, os.R_OK):
            response, bodySize = getForbiddenResponse(httpVersion, restHeaders)
            responseBodySize = bodySize
            response = response.encode('ISO-8859-1')
        else:
            if STATUSCODE != 404 and "If-Modified-Since" in restHeaders and restHeaders["If-Modified-Since"].lstrip() == lastModified:
                STATUSCODE = 304
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                if "Content-Type" in Response:
                    del Response["Content-Type"]
                if "Content-Length" in Response:
                    del Response["Content-Length"]
                if "Last-Modified" in Response:
                    del Response["Last-Modified"]
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
                response = response.encode('ISO-8859-1')
            else:
                try:
                    requestedFile = open(newRequestedPath, "rb")
                    with requestedFile:
                        finalFile = requestedFile.read()
                except Exception as error:
                    # writeErrorLog("error", error)
                    pass
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                Response["Content-Type"] = switchContentType(fileExtension)
                Response["Content-Length"] = str(len(finalFile))
                Response["Last-Modified"] = lastModified
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
                response += "\r\n"
                responseBodySize = Response["Content-Length"]
                response = response.encode('ISO-8859-1') + finalFile
    else:
        newRequestedPath, fileExtension, lastModified = getRequestedFile(
            requestedPath, "r")
        if not os.access(newRequestedPath, os.R_OK):
            response, bodySize = getForbiddenResponse(httpVersion, restHeaders)
            responseBodySize = bodySize
        else:
            if STATUSCODE != 404 and "If-Modified-Since" in restHeaders and restHeaders["If-Modified-Since"].lstrip() == lastModified:
                STATUSCODE = 304
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                if "Content-Type" in Response:
                    del Response["Content-Type"]
                if "Content-Length" in Response:
                    del Response["Content-Length"]
                if "Last-Modified" in Response:
                    del Response["Last-Modified"]
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
            else:
                try:
                    requestedFile = open(newRequestedPath, "r")
                    with requestedFile:
                        finalFile = requestedFile.read()
                except Exception as error:
                    # writeErrorLog("error", error)
                    pass
                response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
                Response["Content-Type"] = switchContentType(fileExtension)
                Response["Content-Length"] = str(len(finalFile))
                Response["Last-Modified"] = lastModified
                Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
                for key, value in Response.items():
                    response += str(key) + ": " + str(value) + "\r\n"
                response += "\r\n" + finalFile
                responseBodySize = Response["Content-Length"]

        # print("RESPONSE BEFORE ENCODING: ", response)

        response = response.encode('ISO-8859-1')
    writeAccessLog("GET", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handlePOSTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, imageFileExtensions, CONFIG, CLIENTIP
    finalFile = "<!DOCTYPE html><html><head><title>POST</title></head><body><h1>POST Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 201
    if "filename" in requestBody:
        # tName = requestBody["filename"].split(".")
        resultFile = requestBody["filename"]
        # resultFile = ".".join(tName[0:-1]) + "(Server)." + tName[-1]
        try:
            fileMode = "a"
            fileContent = requestBody[requestBody["filename"]]
            if str(requestBody["filename"]).endswith(tuple(imageFileExtensions)):
                fileMode = "wb"
                fileContent = fileContent.encode('ISO-8859-1')
            if not os.path.isdir(CONFIG['CLIENT']['Directory']):
                os.mkdir(CONFIG['CLIENT']['Directory'])
            with open(CONFIG['CLIENT']['Directory'] + "/" + resultFile, fileMode) as writeFile:
                writeFile.write(fileContent)
        except Exception as error:
            # writeErrorLog("error", error)
            pass
        if requestBody["filename"] in requestBody:
            del requestBody[requestBody["filename"]]
    newPostData = "POST Date: " + Response["Date"] + "\n" + "POST DATA:\n"
    for key, value in requestBody.items():
        newPostData += "\t" + str(key) + " = " + str(value) + "\n"
    newPostData += "\n" + "#"*60 + "\n\n"
    # Response["Content-Location"] = requestedPath
    try:
        if not os.path.isdir(CONFIG['CLIENT']['Directory']):
            os.mkdir(CONFIG['CLIENT']['Directory'])
        with open(CONFIG['CLIENT']['POST'], "a") as outputFile:
            outputFile.write(newPostData)
        # include global CONFIG
        # with open(CONFIG['PATH']['DocumentRoot'] + "/server_data.txt", "a") as outputFile:
        #     outputFile.write(newPostData)
    except Exception as error:
        # writeErrorLog("error", error)
        pass
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    response = response.encode('ISO-8859-1')
    responseBodySize = Response["Content-Length"]
    writeAccessLog("POST", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handleHEADRequest(httpVersion="", restHeaders={}, requestedPath=""):
    global STATUSCODE, imageFileExtensions, Response, CONFIG, CLIENTIP
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    try:
        if os.path.isfile(CONFIG['PATH']['DocumentRoot'] + requestedPath):
            fileExtension = requestedPath.split(".")[-1]
    except Exception as error:
        # writeErrorLog("debug", error)
        pass
    Response["Date"] = httpDateFormat()
    Response["Content-Type"] = switchContentType(fileExtension)
    STATUSCODE = 200
    path = getValidFilePath(requestedPath)
    if not os.access(path, os.R_OK):
        STATUSCODE = 403
        finalFile = "<!DOCTYPE html><html><head><title>Delta-Server</title></head><body><h1>403</h1><h2>Server refuses to process request (restricted resource access)</h2></body></html>"
        Response["Content-Length"] = str(len(finalFile))
    else:
        if path.endswith(('not_found.html')):
            STATUSCODE = 404
        Response["Content-Length"] = str(os.path.getsize(path))
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += str(key) + ": " + str(value) + "\r\n"
    response += "\r\n"
    response = response.encode('ISO-8859-1')
    responseBodySize = Response["Content-Length"]
    writeAccessLog("HEAD", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handlePUTRequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, imageFileExtensions, CLIENTIP
    finalFile = "<!DOCTYPE html><html><head><title>PUT</title></head><body><h1>PUT Success</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    Response["Date"] = httpDateFormat()
    STATUSCODE = 200
    path = "dump.txt"
    fileDataOutput = ""
    exists = True
    if not os.path.exists(requestedPath[1:]) and requestedPath != "/":
        STATUSCODE = 201
        sep = requestedPath.split("/")
        expectedFile = sep[-1].split(".")
        if len(expectedFile) > 1:
            if sep[0] == "":
                path = "/".join(sep[1:-1])
            else:
                path = "/".join(sep[:-1])
            try:
                os.makedirs(path)
            except Exception as error:
                # writeErrorLog("error", error)
                pass
            path += "/" + sep[-1]
        else:
            try:
                if sep[0] == "" and len(sep) > 1:
                    newReqPath = "/".join(sep[1:])
                else:
                    newReqPath = "/".join(sep)
                os.makedirs(newReqPath)
            except Exception as error:
                # writeErrorLog("error", error)
                pass
            path = newReqPath + "/dump.txt"
        exists = False
    if os.path.exists(requestedPath[1:]) and not os.access(requestedPath[1:], os.W_OK):
        response, bodySize = getForbiddenResponse(httpVersion, restHeaders)
        responseBodySize = bodySize
        response = response.encode('ISO-8859-1')
        writeAccessLog("PUT", httpVersion, requestedPath,
                       responseBodySize, restHeaders)
        return response
    if "filename" in requestBody:
        resultFile = requestBody["filename"]
        newPath = ""
        if not exists:
            newPath = "/".join(path.rsplit("/", 1)) + "/"
        elif requestedPath[1:] != "":
            newPath = "/".join(requestedPath[1:].rsplit("/", 1)) + "/"
        try:
            fileMode = "a"
            fileContent = requestBody[requestBody["filename"]]
            if str(requestBody["filename"]).endswith(tuple(imageFileExtensions)):
                fileMode = "wb"
                fileContent = fileContent.encode('ISO-8859-1')
            with open(newPath + resultFile, fileMode) as writeFile:
                writeFile.write(fileContent)
        except Exception as error:
            # writeErrorLog("error", error)
            pass

        if requestBody["filename"] in requestBody:
            del requestBody[requestBody["filename"]]

    for key, value in requestBody.items():
        fileDataOutput += str(key) + " = " + str(value) + "\n"

    try:
        if exists and requestedPath[1:] != "" and not os.path.isfile(requestedPath[1:]):
            path = requestedPath[1:] + "/dump.txt"
        with open(path, "w") as outputFile:
            outputFile.write(fileDataOutput)
    except Exception as error:
        # writeErrorLog("error", error)
        pass
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    response = response.encode('ISO-8859-1')
    responseBodySize = Response["Content-Length"]
    writeAccessLog("PUT", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def handleDELETERequest(httpVersion="", restHeaders={}, requestedPath="", requestBody={}):
    global Response, STATUSCODE, CLIENTIP
    finalFile = "<!DOCTYPE html><html><head><title>DELETE</title></head><body><h1>Resource Deleted !</h1></body></html>"
    response = ""
    fileExtension = "html"
    responseBodySize = "-"
    try:
        if os.path.isfile(requestedPath[1:]) or os.path.islink(requestedPath[1:]):
            if not os.access(requestedPath[1:], os.W_OK):
                response, bodySize = getForbiddenResponse(
                    httpVersion, restHeaders)
                responseBodySize = bodySize
                response = response.encode('ISO-8859-1')
                writeAccessLog("DELETE", httpVersion,
                               requestedPath, responseBodySize, restHeaders)
                return response
            else:
                STATUSCODE = 200
                os.unlink(requestedPath[1:])
        elif os.path.isdir(requestedPath):
            if not os.access(requestedPath[1:], os.W_OK):
                response, bodySize = getForbiddenResponse(
                    httpVersion, restHeaders)
                responseBodySize = bodySize
                response = response.encode('ISO-8859-1')
                writeAccessLog("DELETE", httpVersion,
                               requestedPath, responseBodySize, restHeaders)
                return response
            else:
                rmtree(requestedPath)
        else:
            STATUSCODE = 404
            finalFile = "<!DOCTYPE html><html><head><title>DELETE</title></head><body><h1>Resource was not present !</h1></body></html>"
    except Exception as error:
        # writeErrorLog("error", error)
        pass
    response = httpVersion + switchStatusCode(STATUSCODE) + "\r\n"
    Response["Content-Type"] = switchContentType(fileExtension)
    Response["Content-Length"] = str(len(finalFile))
    Response["Set-Cookie"] = setCookie(CLIENTIP, restHeaders)
    for key, value in Response.items():
        response += key + ": " + value + "\r\n"
    response += "\r\n" + finalFile
    responseBodySize = Response["Content-Length"]
    response = response.encode('ISO-8859-1')
    writeAccessLog("DELETE", httpVersion, requestedPath,
                   responseBodySize, restHeaders)
    return response


def eachClientThread(clientConnection=None):
    global STATUSCODE
    # totalClientConnections.append(clientConnection)
    try:
        connectionData = clientConnection.recv(1024).decode('ISO-8859-1')
        # print("Received Connection Data: ", connectionData)
        requestedMethod, requestedPath, httpVersion, restHeaders, requestBody = getParsedData(
            connectionData, clientConnection)
        # response = b'HTTP/1.1 200 OK\r\n'
        response, responseBodySize, isValid = validateRequest(
            requestedMethod, httpVersion, restHeaders)
        # print("Response after validation: ", response)
        if isValid:
            if requestedMethod == "GET":
                response = handleGETRequest(
                    httpVersion, restHeaders, requestedPath)
            elif requestedMethod == "POST":
                response = handlePOSTRequest(
                    httpVersion, restHeaders, requestedPath, requestBody)
            elif requestedMethod == "PUT":
                response = handlePUTRequest(
                    httpVersion, restHeaders, requestedPath, requestBody)
            elif requestedMethod == "DELETE":
                response = handleDELETERequest(
                    httpVersion, restHeaders, requestedPath, requestBody)
            elif requestedMethod == "HEAD":
                response = handleHEADRequest(
                    httpVersion, restHeaders, requestedPath)
        else:
            writeAccessLog(requestedMethod, httpVersion,
                           requestedPath, responseBodySize, restHeaders)

        clientConnection.send(response)
        # if clientConnection in totalClientConnections:
        #     totalClientConnections.remove(clientConnection)
        clientConnection.close()

    except Exception as error:
        # writeErrorLog("error", error)
        # break
        pass


def startServer(serverSocket=None):
    global CLIENTIP, CONFIG
    maxConnections = int(CONFIG["CONNECTIONS"]["Allowed"])
    while True:
        try:
            if threading.activeCount() <= maxConnections:
                clientConnection, addr = serverSocket.accept()
                CLIENTIP = str(addr[0])
                forEachConnection = threading.Thread(
                    target=eachClientThread, args=(clientConnection, ))
                forEachConnection.start()
        except Exception as error:
            # writeErrorLog("error", error)
            # break
            pass


def establishConnection():
    global CONFIG
    serverSocket = socket(AF_INET, SOCK_STREAM)
    try:
        serverPort = int(CONFIG.get("DEFAULT", "PORT"))
    except Exception as error:
        print(error, 'of config file.')
        print("Please specify a valid listen port in default section of config file.")
        # writeErrorLog("error", error)
        sys.exit(1)
    try:
        serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        serverSocket.bind(('', serverPort))
        listenToConnections = int(CONFIG["CONNECTIONS"]["Allowed"])
        serverSocket.listen(listenToConnections)
        # serverSocket.listen(int(CONFIG.get("CONNECTIONS", "Allowed")))
    except Exception as error:
        writeErrorLog("error", error)
        pass
    return serverSocket


def clearInvalidLog():
    global CONFIG
    try:
        accessPath = CONFIG['LOG']['Access']
        errorPath = CONFIG['LOG']['Error']
        if(os.path.isfile(accessPath) and os.path.getsize(accessPath) > 100000):
            os.unlink(accessPath)
        if(os.path.isfile(errorPath) and os.path.getsize(errorPath) > 100000):
            os.unlink(errorPath)
    except Exception as error:
        # writeErrorLog("error", error)
        pass


def readConfig():
    global CONFIG
    CONFIG = ConfigParser()
    try:
        if not os.path.isdir('ConfigFiles'):
            os.mkdir("ConfigFiles")
        CONFIG.read('ConfigFiles/config.ini')
        clearInvalidLog()
    except Exception as error:
        writeErrorLog("error", error)
        sys.exit(1)


if __name__ == "__main__":
    readConfig()
    serverSocket = establishConnection()
    # print("The Server is ready to receive requests")
    startServer(serverSocket)
