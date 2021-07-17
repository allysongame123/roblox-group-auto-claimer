import shared
import socket
import ssl
import time

def csrf_refresher(cookie):
    request = (
        "POST /v1/groups/create HTTP/1.1\n"
        "Host:groups.roblox.com\n"
        "Content-Length:0\n"
        f"Cookie:.ROBLOSECURITY={cookie}\n"
        "\n".encode())
    context = ssl.create_default_context()
    while True:
        try:
            _sock = socket.socket()
            _sock.settimeout(5)
            _sock.connect(("groups.roblox.com", 443))
            _sock = context.wrap_socket(_sock, server_hostname="groups.roblox.com")
            _sock.send(request)
            shared.csrf_token = _sock.recv(1024**2).split(b"x-csrf-token:", 1)[1].split(b"\n", 1)[0].strip().decode()
            _sock.shutdown(socket.SHUT_RDWR)
            _sock.close()
            time.sleep(5)
        except:
            pass

def socket_refresher():
    global sock
    context = ssl.create_default_context()
    while True:
        try:
            _sock = socket.socket()
            _sock.settimeout(5)
            _sock.connect(("groups.roblox.com", 443))
            if shared.sock:
                try:
                    shared.sock.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                shared.sock.close()
            shared.sock = context.wrap_socket(_sock, server_hostname="groups.roblox.com")
            time.sleep(5)
        except:
            pass

def group_claimer(group_queue, token_queue, logs, cookie, user_id):
    global sock
    while True:
        group_id = group_queue.get(True)
        try:
            token, captcha_id = token_queue.get(True, 15)
        except TimeoutError:
            print(f"Skipped group {group_id} because token queue timed out")
            continue

        temp_sock = shared.sock
        shared.sock = None
        try:
            temp_sock.send(
                f"POST /v1/groups/{group_id}/users HTTP/1.1\n"
                "Host:groups.roblox.com\n"
                "Content-Type:application/json\n"
                f"Content-Length:{75+len(captcha_id)+len(token)}\n"
                f"X-CSRF-TOKEN:{shared.csrf_token}\n"
                f"Cookie:.ROBLOSECURITY={cookie}\n"
                "\n"
                f'{{"captchaId":"{captcha_id}","captchaToken":"{token}","captchaProvider":"PROVIDER_ARKOSE_LABS"}}'.encode())
            resp = temp_sock.recv(1024 ** 2).split(b"\r\n\r\n", 1)[1].decode()
            success = resp == "{}"
            logs.appendleft({
                "time": time.time(),
                "action": "join",
                "params": {
                    "groupId": group_id,
                    "success": success,
                    "response": resp
                }
            })

            # joined group successfully
            if success:
                temp_sock.send(
                    f"POST /v1/groups/{group_id}/claim-ownership HTTP/1.1\n"
                    "Host:groups.roblox.com\n"
                    "Content-Type:application/json\n"
                    "Content-Length:2\n"
                    f"X-CSRF-TOKEN:{shared.csrf_token}\n"
                    F"Cookie:.ROBLOSECURITY={cookie}\n"
                    "\n"
                    "{}".encode())
                resp = temp_sock.recv(1024 ** 2).split(b"\r\n\r\n", 1)[1].decode()
                success = resp == "{}"
                logs.appendleft({
                    "time": time.time(),
                    "action": "claim",
                    "params": {
                        "groupId": group_id,
                        "success": success,
                        "response": resp
                    }
                })
                
                # claimed group successfully
                if success:
                    print(f"Claimed group {group_id}")

                # failed to claim group, leave
                else:
                    temp_sock.send(
                        f"DELETE /v1/groups/{group_id}/users/{user_id} HTTP/1.1\n"
                        "Host:groups.roblox.com\n"
                        "Content-Type:application/json\n"
                        "Content-Length:2\n"
                        f"X-CSRF-TOKEN:{shared.csrf_token}\n"
                        f"Cookie:.ROBLOSECURITY={cookie}\n"
                        "\n"
                        "{}".encode())
                    resp = temp_sock.recv(1024 ** 2).split(b"\r\n\r\n", 1)[1].decode()
                    success = resp == "{}"
                    logs.appendleft({
                        "time": time.time(),
                        "action": "leave",
                        "params": {
                            "groupId": group_id,
                            "success": success,
                            "response": resp
                        }
                    })
        except Exception as err:
            print(f"claim error: {err!r}")