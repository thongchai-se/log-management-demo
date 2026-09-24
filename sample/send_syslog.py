import socket

HOST = "127.0.0.1"
PORT = 5514

MESSAGE = (
    "<134>Aug 20 12:44:56 fw01 vendor=demo product=ngfw "
    "action=deny src=10.0.1.10 dst=8.8.8.8 spt=5353 dpt=53 "
    "proto=udp msg=DNS_blocked policy=Block-DNS"
)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(MESSAGE.encode("utf-8"), (HOST, PORT))
sock.close()
print("sent syslog OK")