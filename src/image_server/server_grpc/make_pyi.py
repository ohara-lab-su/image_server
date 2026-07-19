"""grpc_frameのpyi生成機能を使用してクライアントstubを生成する。"""

import importlib
import inspect
from pathlib import Path

from image_server.server_grpc.client import ImageStreamClient
from image_server.server_grpc.image_stream_grpc_service import (
    ImageStreamGrpcService,
)


_GENERATOR_CANDIDATES = (
    ("grpc_frame.make_pyi", "make_pyi"),
    ("grpc_frame.make_pyi", "make_pyi_client"),
    ("grpc_frame.make_pyi", "make_pyi_grpc_client"),
    ("grpc_frame.make_pyi_client", "make_pyi_client"),
    ("grpc_frame.make_pyi_grpc_client", "make_pyi_grpc_client"),
    ("grpc_frame.grpc_client.make_pyi", "make_pyi"),
)


def _load_generator():
    errors = []
    for module_name, function_name in _GENERATOR_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            errors.append("{}: {}".format(module_name, exc))
            continue

        generator = getattr(module, function_name, None)
        if callable(generator):
            return generator

        errors.append(
            "{} has no callable {}".format(
                module_name,
                function_name,
            )
        )

    raise ImportError(
        "grpc_frameのpyi生成関数を検出できませんでした。\n{}".format(
            "\n".join(errors)
        )
    )


def _build_arguments(generator, output_path):
    signature = inspect.signature(generator)
    arguments = {}

    value_map = {
        "filename": str(output_path),
        "file_path": str(output_path),
        "output": str(output_path),
        "output_file": str(output_path),
        "output_path": str(output_path),
        "pyi_path": str(output_path),
        "service_class": ImageStreamGrpcService,
        "service_cls": ImageStreamGrpcService,
        "ctrl_class": ImageStreamGrpcService,
        "ctrl_cls": ImageStreamGrpcService,
        "device_class": ImageStreamGrpcService,
        "device_cls": ImageStreamGrpcService,
        "source_class": ImageStreamGrpcService,
        "source_cls": ImageStreamGrpcService,
        "client_class": ImageStreamClient,
        "client_cls": ImageStreamClient,
        "class_name": "ImageStreamClient",
        "client_class_name": "ImageStreamClient",
        "module_name": "image_server.server_grpc.client",
    }

    for name, parameter in signature.parameters.items():
        if name in value_map:
            arguments[name] = value_map[name]
            continue

        if parameter.default is inspect.Parameter.empty:
            raise TypeError(
                "grpc_frame pyi生成関数の必須引数に対応できません: "
                "{}{}".format(generator.__name__, signature)
            )

    return arguments


def main():
    base_dir = Path(__file__).resolve().parent
    output_path = base_dir / "client.pyi"

    generator = _load_generator()
    arguments = _build_arguments(generator, output_path)
    result = generator(**arguments)

    if not output_path.exists():
        if isinstance(result, str):
            output_path.write_text(result, encoding="utf-8")
        else:
            raise RuntimeError(
                "pyi生成関数は正常終了しましたが、{}が生成されませんでした。"
                .format(output_path)
            )

    print("generated: {}".format(output_path))


if __name__ == "__main__":
    main()
