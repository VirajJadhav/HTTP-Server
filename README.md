# HTTP Server

A **HTTP** or a web **server** is a software that processes requests via **HTTP** , i.e. a network protocol used to exchange information on the World Wide Web (WWW). It's main function is to store, process and deliver web pages / responses / answers to the requests offered / made by a client and fulfill it accordingly.

This project is a rudimentary implementation of how a **HTTP** (**HTTP/1.1** with non - persistent connections with client) server performs / answers to **HTTP** requests from client.
(Here, client:- Anyone who can establish a **TCP** connection with the server and is capabable of sending **HTTP** requests as well receiving a **HTTP** response)

## To run this project

**Requirements:**

1. python installed (version >= 3.8)
2. python packages - (socket, threading, datetime, email.utils, sys, os, configparser, shutil, uuid, json, requests)

**Steps To Run:**

- Server:
  `sudo python3 main.py <options>`

  1. \<options>
     - To start server: start | START
       - `sudo python3 main.py start`
         or
       - `sudo python3 main.py START`
     - To stop server: stop | STOP
       - `sudo python3 main.py stop`
         or
       - `sudo python3 main.py STOP`
     - To restart server: restart | RESTART
       - `sudo python3 main.py restart`
         or
       - `sudo python3 main.py RESTART`

- Client Tester:
  1. Load Testing
     - `python3 client_test.py -l <number-of-requests>`
       - Options
         - -l, --load
         - --debug=True (For logging response codes on terminal for respective request methods)
       - \<number-of-requests> (optional) : Integer value for multiple same requests present in **LTest.json** file.
         Default value: Number of request objest present in **LTest.json**.
  2. Confirmation Testing
     - `python3 client_test.py -c <method-name>`
       - Options
         - -c, --confirmation
         - --debug=True (For logging response codes on terminal for respective request methods)
       - \<method-name> : **GET** | **POST** | **PUT** | **DELETE** | **HEAD** (requests present / to be added in **CTest.json** file)

## Important file Syntax

1. CTest.json or LTest.json (For testing purpose)
   - possible keys (case-sensitive):
     - "method": which states HTTP method ("GET", "POST", "PUT", "DELETE", "HEAD")
     - "url": url to which the request is sent ("/index.html", "/something", etc); (Default is "/")
     - "data" (Applicable for POST and PUT): Again in key, value pairs.
     - "file" (Applicable for POST and PUT): Again in key, value pais.
         - "name": filename that is expected to be stored on server 
         - "path": file path from where the client is expected to pick the file (Absolute path is expected) 
         - "fileType" (options): eg = ("text", "image"); (Default is "_/_")
    
   - possible values:
     - Anything with well defined and valid characters.
     
      example:-
      
  >         {
  >            "method": "POST",
  >            "url": "/something",
  >            "data" = {
  >             "name": "Delta-server",
  >             "location": "pune",
  >             .
  >             .
  >             .
  >           },
  >            "file" = {
  >              "name": "serverToBeuploaded.txt",
  >              "path": "/home/USER/Desktop/somefile.txt",
  >              "fileType": "text"
  >           }
  >         },         
  >         {
  >            "method": "GET",
  >            "url": "/index.html"
  >         }

2. config.ini (Config file)
   - Present in ConfigFiles/config.ini or (\<absolute-path>/ConfigFiles/config.ini)
   - **Syntax**
     ```
     [SECTION]
     key = value
     eg,
     [DEFAULT]
     PORT = 4000
     ```

## References  
  RFC 2612 - https://tools.ietf.org/html/rfc2616
  
  Python Docs - https://docs.python.org/3/
