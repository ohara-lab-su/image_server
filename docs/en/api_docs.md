# API overview

## ImageStreamCtrl

Main methods:

- `open()`
- `close()`
- `read()`
- `grab()`
- `is_open()`

Responsible only for local camera control.

## ImageStreamGrpcService

- gRPC server
- EventBus registration
- JPEG delivery
- Streaming loop

## ImageStreamClient

- `connect()`
- `disconnect()`
- `get_frame()`

Provides a synchronous client interface.

## make_pyi.py

Generates `client.pyi` to support IDE completion.

For module-level references, see the automatically generated API pages.
