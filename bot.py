from structures import ExpiringQueue
from threads import socket_refresher, csrf_refresher, group_claimer
from web import create_app
from queue import Queue
from urllib.parse import urlencode
from collections import deque
from flask import Flask, request, render_template, jsonify
import threading
import socket
import ssl
import json
import time

group_queue = Queue()
token_queue = ExpiringQueue(max_size=5, ttl=120)
logs = deque(maxlen=100)

# load cookie from file
with open("cookie.txt") as fp:
    cookie = fp.read().strip().split("_")[-1]

# get user id
with socket.create_connection(("users.roblox.com", 443)) as sock:
    sock = ssl.wrap_socket(sock)
    sock.send(
        "GET /v1/users/authenticated HTTP/1.1\n"
        "Host:users.roblox.com\n"
        f"Cookie:.ROBLOSECURITY={cookie}\n"
        "\n".encode())
    user_id = json.loads(sock.recv(1024**2).split(b"\r\n\r\n", 1)[1])["id"]
    sock.shutdown(socket.SHUT_RDWR)

app = create_app(**globals())
threading.Thread(target=socket_refresher).start()
threading.Thread(target=csrf_refresher, args=(cookie,)).start()
threading.Thread(target=group_claimer, args=(
    group_queue, token_queue, logs, cookie, user_id)).start()
threading.Thread(target=app.run, kwargs={"port": 8080}).start()