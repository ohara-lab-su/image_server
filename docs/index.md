# image_server

画像転送プログラムの基本となる雛形

---
```{toctree}
:maxdepth: 2
:caption: Contents:

api/modules
tutorials/tutorial
api_docs
```

## 設計思想

本ライブラリは「画像取得」と「画像配信」を独立した責務として設計しています。

### ImageStreamCtrl

- カメラを開く
- フレーム取得
- 解像度変更
- OpenCV のみ利用

### ImageStreamGrpcService

- gRPC サービス
- EventBus
- JPEG エンコード
- クライアント配信

この分離により、ローカルアプリケーションは OpenCV のみで利用でき、
ネットワーク配信は gRPC 層だけを交換できます。
