# from https://gist.github.com/miloszw/f3ed3f5fd30fac85f1df

# Also looked at https://gist.github.com/SevenW/47be2f9ab74cac26bf21
# and https://gist.github.com/jkp/3136208

# This looks like what we are basically wanting to do: https://github.com/SevenW/Plugwise-2-py

import struct
import SocketServer
import sys
from base64 import b64encode
from hashlib import sha1
from mimetools import Message
from StringIO import StringIO

DEFAULT_PORT = 9999


########################################################################
class WebSocketsHandler(SocketServer.StreamRequestHandler):
    magic = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'

    ####################################################################
    def setup(self):
        SocketServer.StreamRequestHandler.setup(self)
        print "connection established", self.client_address
        self.handshake_done = False

    ####################################################################
    def handle(self):
        while True:
            if not self.handshake_done:
                self.handshake()
            else:
                self.read_next_message()

    ####################################################################
    def read_next_message(self):
        length = ord(self.rfile.read(2)[1]) & 127
        if length == 126:
            length = struct.unpack(">H", self.rfile.read(2))[0]
        elif length == 127:
            length = struct.unpack(">Q", self.rfile.read(8))[0]
        masks = [ord(byte) for byte in self.rfile.read(4)]
        decoded = ""
        for char in self.rfile.read(length):
            decoded += chr(ord(char) ^ masks[len(decoded) % 4])
        self.on_message(decoded)

    ####################################################################
    def send_message(self, message):
        self.request.send(chr(129))
        length = len(message)
        if length <= 125:
            self.request.send(chr(length))
        elif length >= 126 and length <= 65535:
            self.request.send(126)
            self.request.send(struct.pack(">H", length))
        else:
            self.request.send(127)
            self.request.send(struct.pack(">Q", length))
        self.request.send(message)

    ####################################################################
    def handshake(self):
        data = self.request.recv(1024).strip()
        headers = Message(StringIO(data.split('\r\n', 1)[1]))
        if headers.get("Upgrade", None) != "websocket":
            return
        print 'Handshaking...'
        key = headers['Sec-WebSocket-Key']
        digest = b64encode(sha1(key + self.magic).hexdigest().decode('hex'))
        response = 'HTTP/1.1 101 Switching Protocols\r\n'
        response += 'Upgrade: websocket\r\n'
        response += 'Connection: Upgrade\r\n'
        response += 'Sec-WebSocket-Accept: %s\r\n\r\n' % digest
        self.handshake_done = self.request.send(response)

    ####################################################################
    def on_message(self, message):
        pass # overridden by WebSocketServer


########################################################################
class WebSocketServer(SocketServer.TCPServer):
    ####################################################################
    def __init__(self, port, on_message):
        WebSocketsHandler.on_message = on_message
        SocketServer.TCPServer.__init__(self, ("localhost", port), WebSocketsHandler)

    ####################################################################
    def serve(self):
        try:
            self.serve_forever()
        except KeyboardInterrupt:
            print "Shutting down.."
            self.shutdown()

########################################################################
if __name__ == "__main__":
    try:
        port = int(sys.argv[1])
    except:
        port = DEFAULT_PORT

    def simple_print(self, message):
        print message
    WebSocketServer(port, simple_print).serve()