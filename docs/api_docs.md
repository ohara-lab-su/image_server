# API

## ImageStreamCtrl

主要メソッド

- open()
- close()
- read()
- grab()
- is_open()

役割はローカルカメラ制御のみです。

## ImageStreamGrpcService

- gRPC サーバ
- EventBus 登録
- JPEG 配信
- 配信ループ

## ImageStreamClient

- connect()
- disconnect()
- get_frame()

同期クライアントとして利用します。

## make_pyi.py

client.pyi を生成し、IDE 補完を提供します。
