#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ImageStreamClientの型スタブを生成する。"""

import inspect
from pathlib import Path

from grpc_frame.grpc_client import SyncGrpcClient
from grpc_frame.make_pyi import generate_client_pyi


CLIENT_CLASS_NAME = "ImageStreamClient"
CTRL_CLASS_NAME = "ImageStreamGrpcService"
BASE_CLASS_NAME = "SyncGrpcClient"


def main():
    """grpc_frameのgenerate_client_pyi()でclient.pyiを生成する。"""
    current_dir = Path(__file__).resolve().parent
    grpc_client_file = Path(inspect.getfile(SyncGrpcClient)).resolve()

    generate_client_pyi(
        client_py=current_dir / "client.py",
        client_class=CLIENT_CLASS_NAME,
        ctrl_py=current_dir / "image_stream_grpc_service.py",
        ctrl_class=CTRL_CLASS_NAME,
        base_py=grpc_client_file,
        base_class=BASE_CLASS_NAME,
        out_path=current_dir / "client.pyi",
    )

    print("generated: {}".format(current_dir / "client.pyi"))


if __name__ == "__main__":
    main()
