# Tutorial

## 1. ローカルで画像取得

```python
from image_server.image_stream_ctrl import ImageStreamCtrl

cam=ImageStreamCtrl()
cam.open()

while True:
    frame=cam.read()
```

## 2. サーバ起動

```
python examples/run_image_server.py
```

ImageStreamGrpcService が ImageStreamCtrl を生成し、
取得した画像をクライアントへ配信します。

## 3. クライアント

```python
from image_server.server_grpc.client import ImageStreamClient

client=ImageStreamClient(...)
client.connect()
```

## 4. Viewer

```
python examples/image_viewer_gui.py
```

GUI は受信した画像をリアルタイム表示します。
