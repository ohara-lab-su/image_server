# image_server

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/image_server/blob/main/README.en.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/image_server/blob/main/README.md)


image_server は「USBカメラを扱うライブラリ」ではありません。

本ライブラリは **画像転送機能を既存プログラムへ組み込むためのテンプレート** です。
OpenCV・gRPC・Viewer を毎回実装するのではなく、画像取得部分だけを書き換えることで
画像転送システムを短時間で構築できることを目的としています。

## このライブラリが解決する問題

通常は次のような処理を毎回実装する必要があります。

- カメラ接続
- フレーム取得
- JPEG圧縮
- 通信
- Viewer
- 接続管理
- スレッド管理

image_server はこれらを共通化し、利用者は **画像取得部だけ** を実装します。

## レイヤ構造

Application
↓
ImageStreamGrpcService
↓
ImageStreamCtrl
↓
Camera SDK

ImageStreamCtrl は Camera SDK を抽象化する層です。
ImageStreamGrpcService は画像配信だけを担当します。

## 開発フロー

1. ImageStreamCtrl を OpenCV で動かす
2. SDK に置き換える
3. run_image_server.py を起動
4. Viewer で確認
5. DeviceProxy や AI システムへ組み込む

## 想定用途

- USB Camera
- Basler
- IDS
- HikVision
- GigE Vision
- ORiN Camera
- AI 推論サーバ
- 外観検査
- ロボットビジョン
