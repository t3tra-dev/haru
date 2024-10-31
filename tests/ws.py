from haru import Haru, WebSocketServerProtocol, upgrade_websocket

app = Haru(__name__)


@app.route("/ws")
@upgrade_websocket
async def ws(websocket: WebSocketServerProtocol):
    print("Connection opened")
    try:
        async for message in websocket:
            print(f"Message from client: {message}")
            await websocket.send("Hello from server!")
    except Exception as e:
        raise e
    finally:
        print("Connection closed")


app.run()
