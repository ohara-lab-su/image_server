# image_server

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://ohara-lab-su.github.io/image_server/)
[![ja](https://img.shields.io/badge/lang-ja-red.svg)](https://ohara-lab-su.github.io/image_server/ja/)

[![GitHub](https://img.shields.io/badge/GitHub-ohara--lab--su%2Fimage_server-181717?logo=github)](https://github.com/ohara-lab-su/image_server/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Documentation-222222?logo=githubpages&logoColor=white)](https://ohara-lab-su.github.io/image_server/en/)
[![Ohara Lab](https://img.shields.io/badge/Ohara%20Lab-Home-4B5563?logo=homeassistant&logoColor=white)](https://ohara-lab-su.github.io/index.en.html)

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
