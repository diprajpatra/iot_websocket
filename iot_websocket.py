# ---------------------------------------------
# This python code is written by Dipraj Patra.
# ---------------------------------------------
import asyncio
import websockets
import json
import os


All_User = set()
MAX_HEADERS = 256


class HttpWebsocket(websockets.WebSocketServerProtocol):
    ws_object = None
    USERS = set()

    async def handler(self):

        try:
            # Extracting request_line and header from Stream reader.
            request_line = await websockets.http.read_line(self.reader)
            print(request_line)
            headerlist = []
            for num in range(MAX_HEADERS):
                header_line = await websockets.http.read_line(self.reader)
                print(header_line.decode())
                headerlist.append(header_line)
                if header_line == b'':
                    break
            else:
                raise ValueError("Too many headers")

            # Extracting http method path and version from request_line
            # eg, GET /ws http/1.1
            method, path, version = request_line.decode().split(None, 2)
            print(method)
            print(path)
            print(version)

        except Exception as e:
            print(e.args)
            self.transport.close()
            self.ws_server.unregister(self)

            raise
        if path == '/ws':
            # Putting the request_line and header data back, So that the class: server.
            # def: handler can connect to a web socket clint.
            self.reader.feed_data(request_line + b'\r\n')
            for u in range(len(headerlist)):
                self.reader.feed_data(headerlist[u] + b'\r\n')

            return await super(HttpWebsocket, self).handler()
        else:
            try:
                return await self.body_handler(method, path, version)
            except Exception as e:
                print(e)
            finally:

                self.transport.close()
                self.ws_server.unregister(self)

    async def body_handler(self, method, path, version):
        response = ''
        try:
            # This method will print and send the http body data which you will receive from
            # IFTTT or google api through a HTTP Post request.
            http_body_request = self.reader._buffer.decode('utf-8')
            print("Req-->" + http_body_request)
            message = json.dumps(http_body_request)

            if HttpWebsocket.USERS:  # asyncio.wait doesn't accept an empty list
                await asyncio.wait([user.send(message) for user in HttpWebsocket.USERS])

            # sending 200 ok response to Ifttt or Google api.
            response = '\r\n'.join([
                'HTTP/1.1 200 OK',
                'Content-Type: text/json',
                '',
                'Done',
            ])

        except Exception as e:
            print(e)
        self.transport.write(response.encode())


async def register(websocket):
    # Registering the websocket clients
    global All_User
    HttpWebsocket.USERS.add(websocket)
    All_User.add(websocket)


async def unregister(websocket):
    # We are going to Unregister a websocket clients when it
    # disconnected from server.
    HttpWebsocket.USERS.remove(websocket)
    await All_User.remove(websocket)


async def ws_handler(websocket, path):
    await register(websocket)
    try:
        async for name in websocket:
            # This function will broadcast the http post message
            # as well as the the message which you may receive from
            # a websocket client to every available clients.
            All_User.remove(websocket)
            print("message arrived from ", websocket)
            print("message is ", name)

            await asyncio.wait([user.send(name) for user in All_User])

            All_User.add(websocket)

    finally:
        await unregister(websocket)


port = int(os.getenv('PORT', 5600))  # 5600
print(port)
start_server = websockets.serve(ws_handler, '', port, klass=HttpWebsocket)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
