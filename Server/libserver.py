import sys
import selectors
import json
import io
import struct

import libtrolley

request_search = {
    "morpheus": "Follow the white rabbit. \U0001f430",
    "ring": "In the caves beneath the Misty Mountains. \U0001f48d",
    "\U0001f436": "\U0001f43e Playing ball! \U0001f3d0",
}


class Message:
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._jsonheader_len = None
        self.jsonheader = None
        self.request = None
        self.response_created = False
        self.dataPackage = None
        self.MAC = None
        self.RSSIs = None
        self.BSSIDs = None

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)
    
    def printData(self):
        print('Data received, Length: ', len(self._recv_buffer))
        length = len(self._recv_buffer)
        numWiFi = (length - 6) // 7
        for i in range(len(self._recv_buffer)-numWiFi):
            if i < 6 + 6 * numWiFi:
                print(hex(self._recv_buffer[i]), end=' ')
            # else:
            #     print(self._recv_buffer[i], end=' ')
            if (i+1) % 6 == 0:
                if i == 5:
                    print()
                else:
                    print('\t(', self._recv_buffer[6+6*numWiFi+(i-6)//6], ')')
        print()

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(1024)

        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass    
        else:
            if data:
                self._recv_buffer += data
                # self.printData()
                
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("sending", repr(self._send_buffer), "to", self.addr)
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                # Close when the buffer is drained. The response has been sent.
                if sent and not self._send_buffer:
                    self.close()

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message(self, *, content_bytes, content_type, content_encoding):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def _create_response_json_content(self):
        action = self.request.get("action")
        if action == "search":
            query = self.request.get("value")
            answer = request_search.get(query) or f'No match for "{query}".'
            content = {"result": answer}
        else:
            content = {"result": f'Error: invalid action "{action}".'}
        content_encoding = "utf-8"
        response = {
            "content_bytes": self._json_encode(content, content_encoding),
            "content_type": "text/json",
            "content_encoding": content_encoding,
        }
        return response

    def _create_response_binary_content(self):
        response = {
            "content_bytes": b"First 10 bytes of request: "
            + self.request[:10],
            "content_type": "binary/custom-server-binary-type",
            "content_encoding": "binary",
        }
        return response

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        # if mask & selectors.EVENT_WRITE:
        #     self.write()

    def read(self):
        self._read()

        # if self._recv_buffer is not None:
        #     self.process_data()

        # if self._jsonheader_len is None:
        #     self.process_protoheader()

        # if self._jsonheader_len is not None:
        #     if self.jsonheader is None:
        #         self.process_jsonheader()

        # if self.jsonheader:
        #     if self.request is None:
        #         self.process_request()

    def write(self):
        if self.request:
            if not self.response_created:
                self.create_response()

        self._write()

    def close(self):
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_request(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.request = self._json_decode(data, encoding)
            print("received request", repr(self.request), "from", self.addr)
        else:
            # Binary or unknown content-type
            self.request = data
            print(
                f'received {self.jsonheader["content-type"]} request from',
                self.addr,
            )
        # Set selector to listen for write events, we're done reading.
        self._set_selector_events_mask("w")
    
    def create_response(self):
        if self.jsonheader["content-type"] == "text/json":
            response = self._create_response_json_content()
        else:
            # Binary or unknown content-type
            response = self._create_response_binary_content()
        message = self._create_message(**response)
        self.response_created = True
        self._send_buffer += message

    def macCompare(self, mac, Array):
        flag = True
        for i in range(0,len(Array)):
            flag = True
            for j in range(0,len(Array[0])):
                if Array[i][j] != mac[j]:
                    flag = False
                    break
            if flag:
                return i
        return -1
    
    def macCompare2(self, mac1, mac2):
        flag = True
        for i in range(0,6):
            if mac1[i] != mac2[i]:
                flag = False
                break
        return flag

    def process_data(self, trolleylist: 'list[libtrolley.Trolley]', BeaconXs, BeaconYs, Beacons):
        length = len(self._recv_buffer)
        info = self._recv_buffer
        self._recv_buffer = self._recv_buffer[length:]
        if length % 7 == 6:
            wifis = (length - 6) // 7
            myMac = info[:6]
            info = info[6:]
            id = -1
            for i in range(0, len(trolleylist)):
                if self.macCompare2(myMac, trolleylist[i].MAC):
                    id = i
                    break
            if id == -1:
                id = len(trolleylist)
                trolleylist.append(libtrolley.Trolley(myMac, id, BeaconXs, BeaconYs, Beacons))
            samples = 3
            trolleylist[id].update(info, wifis, BeaconXs, BeaconYs, Beacons, samples)
            if trolleylist[id].loopCount >= samples:
                trolleylist[id].locate()
            trolleylist[id].printInfo(samples)
            # trolleylist[id].only1(Beacons[3])
            


            

            