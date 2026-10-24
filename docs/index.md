# image_server

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/image_server/) [![ja](https://img.shields.io/badge/lang-ja-red.svg)](https://ohara-lab-su.github.io/image_server/ja/)

[GitHub](https://github.com/ohara-lab-su/image_server/) / [Ohara Lab documentation](https://ohara-lab-su.github.io/)

A reusable starting point for image acquisition and gRPC-based image streaming applications. The local camera controller and the network delivery service are separate components.

```{toctree}
:maxdepth: 2
:caption: Contents

tutorial
api_docs
api/modules
```

## Architecture

### ImageStreamCtrl

Handles camera access and local frame acquisition through OpenCV, including opening the device, reading frames and changing resolution. It does not require the gRPC streaming layer.

### ImageStreamGrpcService

Provides the gRPC service, EventBus integration, JPEG encoding and client-side frame delivery. The service uses the camera controller for acquisition.

Separating acquisition from delivery allows local applications to use the camera without a network service and permits the transport layer to evolve independently.
