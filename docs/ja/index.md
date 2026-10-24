# image_server

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/image_server/) [![ja](https://img.shields.io/badge/lang-ja-red.svg)](https://ohara-lab-su.github.io/image_server/ja/)

[GitHub](https://github.com/ohara-lab-su/image_server/) / [ohara-lab-su ドキュメント](https://ohara-lab-su.github.io/)

画像取得と gRPC による画像配信を行うアプリケーションのための基本的な雛形です。ローカルのカメラ制御とネットワーク配信を独立した責務として設計しています。

```{toctree}
:maxdepth: 2
:caption: 目次

tutorial
api_docs
api/modules
```

## 設計思想

### ImageStreamCtrl

OpenCV を利用してカメラのオープン、フレーム取得、解像度変更などを行います。gRPC の配信層を必要としません。

### ImageStreamGrpcService

gRPC サービス、EventBus との連携、JPEG エンコードおよびクライアントへのフレーム配信を担当します。画像取得にはカメラ制御クラスを利用します。

この分離により、ローカルアプリケーションではネットワーク機能なしで画像を扱うことができ、配信方式も独立して変更できます。
