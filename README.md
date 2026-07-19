# image_server

ローカル画像取得層と `grpc_frame` 公開層を分離した汎用画像サーバーです。

```text
src/image_server/
├── __init__.py
├── image_stream_ctrl.py
└── server_grpc/
    ├── __init__.py
    ├── client.py
    └── image_stream_grpc_service.py
```

`image_stream_ctrl.py` は OpenCV のみに依存し、`grpc_frame` を import しません。
JPEG変換、EventBus、配信スレッドは `server_grpc` 内だけにあります。

## ローカル実行

```bash
python examples/local_image_viewer.py
```

## gRPCサーバー

```bash
python examples/run_image_server.py --auto-start
```

## CLI

```bash
python examples/image_client_cli.py status
python examples/image_client_cli.py show
```

## GUI

Python 3.6対応のため、GUIは PySide6 ではなく PyQt5 を使用します。

```bash
python examples/image_viewer_gui.py
```
