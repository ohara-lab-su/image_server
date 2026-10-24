# Tutorial

## 1. Acquire frames locally

```python
from image_server.image_stream_ctrl import ImageStreamCtrl

cam = ImageStreamCtrl()
cam.open()

while True:
    frame = cam.read()
```

## 2. Start the server

```console
python examples/run_image_server.py
```

`ImageStreamGrpcService` creates an `ImageStreamCtrl` instance and streams captured images to clients.

## 3. Connect a client

```python
from image_server.server_grpc.client import ImageStreamClient

client = ImageStreamClient(...)  # Supply the parameters required by your deployment.
client.connect()
```

## 4. Start the viewer

```console
python examples/image_viewer_gui.py
```

The GUI displays incoming images in real time.

The example paths and client constructor arguments must be verified against the actual repository before use.
