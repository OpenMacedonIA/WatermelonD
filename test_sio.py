import socketio
import time
sio = socketio.Client(ssl_verify=False)
try:
    sio.connect('https://localhost:5000', transports=['polling'])
    print("HTTPS CONNECTED")
    sio.disconnect()
except Exception as e:
    print("HTTPS FAILED:", e)
