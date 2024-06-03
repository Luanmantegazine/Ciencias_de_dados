import socket
import threading
import sys
import gzip
import os

def handle(client, directory):
    try:
        request = client.recv(1024)
        if not request:
            return
        fields = request.split(b"\r\n")
        request_line = fields[0].decode()
        method, path, _ = request_line.split()
        
        headers = {}
        for field in fields[1:]:
            if b": " in field:
                key, value = field.split(b": ", 1)
                headers[key.lower()] = value

        if path == "/":
            response = b"HTTP/1.1 200 OK\r\n\r\n"
            client.sendall(response)
        elif path.startswith("/echo"):
            handle_echo(client, path, headers)
        elif path.startswith("/user-agent"):
            handle_user_agent(client, headers)
        elif path.startswith("/files"):
            if method == "GET":
                handle_get_file(client, path, directory)
            elif method == "POST":
                handle_post_file(client, path, directory, request)
        else:
            client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")
    except Exception as e:
        print(f"Error handling request: {e}")
        client.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
    finally:
        client.close()

def handle_echo(client, path, headers):
    echo = path.split("/")[2].encode()
    if b"accept-encoding" in headers and b"gzip" in headers[b"accept-encoding"]:
        echo = gzip.compress(echo)
        content_encoding = b"Content-Encoding: gzip\r\n"
    else:
        content_encoding = b""
    response = (
        b"HTTP/1.1 200 OK\r\n"
        b"Content-Type: text/plain\r\n"
        b"Content-Length: " + str(len(echo)).encode() + b"\r\n"
        + content_encoding +
        b"\r\n" + echo
    )
    client.sendall(response)

def handle_user_agent(client, headers):
    if b"user-agent" in headers:
        agent = headers[b"user-agent"]
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: text/plain\r\n"
            b"Content-Length: " + str(len(agent)).encode() + b"\r\n"
            b"\r\n" + agent
        )
        client.sendall(response)
    else:
        client.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")

def handle_get_file(client, path, directory):
    filename = path.split("/")[2]
    file_path = os.path.join(directory, filename)
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            data = f.read()
        response = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/octet-stream\r\n"
            b"Content-Length: " + str(len(data)).encode() + b"\r\n"
            b"\r\n" + data
        )
        client.sendall(response)
    else:
        client.sendall(b"HTTP/1.1 404 Not Found\r\n\r\n")

def handle_post_file(client, path, directory, request):
    filename = path.split("/")[2]
    file_path = os.path.join(directory, filename)
    body = request.split(b"\r\n\r\n")[1]
    try:
        with open(file_path, "wb") as f:
            f.write(body)
        client.sendall(b"HTTP/1.1 201 Created\r\n\r\n")
    except Exception as e:
        print(f"Error writing file: {e}")
        client.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")

def main():
    directory = "./test"
    if "--directory" in sys.argv:
        directory = sys.argv[sys.argv.index("--directory") + 1]
    port = 4221
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    
    try:
        server_socket = socket.create_server(("localhost", port), reuse_port=True)
        print(f"Server started on port {port}")
        while True:
            client, _ = server_socket.accept()
            threading.Thread(target=handle, args=(client, directory)).start()
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()