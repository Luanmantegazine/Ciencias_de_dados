import socket
import sys

def handle_requests(client_socket):
    try:
        data = client_socket.recv(1024)
        if not data:
            return
        response = parse_request(data)
        client_socket.sendall(response.encode())
    except Exception as e:
        print(f"Error handling request: {e}")
    finally:
        client_socket.close()

def parse_request(data):
    try:
        request_data = data.decode().split("\r\n")
        request_line = request_data[0]
        method, path, http_version = request_line.split()

        if method == "POST" and path == "/":
            # Process the body of the POST request
            body = request_data[-1]  # This is a simplified way to get the body; in practice, you might need more robust handling
            return "HTTP/1.1 200 OK\r\n\r\n"

        elif method == "GET" and path == "/":
            return "HTTP/1.1 200 OK\r\n\r\nHello, World!"

        elif method == "GET" and path.startswith("/echo/"):
            return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(path[6:])}\r\n\r\n{path[6:]}"

        elif method == "GET" and path.startswith("/user-agent"):
            user_agent = None
            for header in request_data:
                if header.lower().startswith("user-agent:"):
                    user_agent = header.split(":", 1)[1].strip()
                    break
            if user_agent:
                return f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {len(user_agent)}\r\n\r\n{user_agent}"
            else:
                return "HTTP/1.1 400 Bad Request\r\n\r\nUser-Agent header not found"

        elif method == "POST" and path.startswith("/files"):
            directory = sys.argv[2]
            filename = path[7:]
            file_path = f"{directory}/{filename}"
            print("File Path: ", file_path)
            try:
                with open(file_path, "w") as f:
                    body = request_data[-1]  # Assuming body is the last part of the data
                    f.write(body)
                    return "HTTP/1.1 201 Created\r\n\r\n"
            except FileNotFoundError:
                return "HTTP/1.1 404 Not Found\r\n\r\n"

        elif method == "GET" and path.startswith("/files"):
            directory = sys.argv[2]
            filename = path[7:]
            file_path = f"{directory}/{filename}"
            try:
                with open(file_path, "r") as f:
                    body = f.read()
                return f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {len(body)}\r\n\r\n{body}"
            except FileNotFoundError:
                return "HTTP/1.1 404 Not Found\r\n\r\n"

        else:
            return "HTTP/1.1 404 Not Found\r\n\r\nNot Found"

    except Exception as e:
        print(f"Error parsing request: {e}")
        return "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"

def main():
    print("Server is starting...")
    server_socket = socket.create_server(("localhost", 4221))
    server_socket.listen()

    try:
        while True:
            client_socket, address = server_socket.accept()
            print(f"Connection from {address}")
            handle_requests(client_socket)
    except KeyboardInterrupt:
        print("Server is shutting down...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    main()