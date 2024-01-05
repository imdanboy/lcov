#!/usr/bin/env python3

import sys
import socket
import selectors
import types
import os

sel = selectors.DefaultSelector()

def start_connections(host, port, cword):
    server_addr = (host, port)
    pid = os.getpid()
    print(f"Starting connection {pid} to {server_addr}", file=sys.stderr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(server_addr)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    data = types.SimpleNamespace(
        pid=pid,
        outb=cword.encode(),
        inb=b"",
    )
    sel.register(sock, events, data=data)

def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            print(f"Received {recv_data!r} from connection {data.pid}", file=sys.stderr)
            data.inb += recv_data
        if len(data.inb) > 3 and data.inb[-3:] == b'EOF':
            print(f"{data.inb[:-3].decode()}") # print g2p result
            recv_data = b""
        if not recv_data:
            print(f"Closing connection {data.pid}", file=sys.stderr)
            sel.unregister(sock)
            sock.close()
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print(f"Sending {data.outb!r} to connection {data.pid}", file=sys.stderr)
            sock.sendall(data.outb + b"EOF")  # Should be ready to write
            data.outb = b""

def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <host> <port> <cword>", file=sys.stderr)
        sys.exit(1)

    host, port, cword = sys.argv[1:4]
    start_connections(host, int(port), cword)

    try:
        while True:
            events = sel.select(timeout=1)
            if events:
                for key, mask in events:
                    service_connection(key, mask)
            # Check for a socket being monitored to continue.
            if not sel.get_map():
                break
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting", file=sys.stderr)
    finally:
        sel.close()

if __name__ == "__main__":
    main()
