# image_server

[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/ohara-lab-su/image_server/blob/main/README.md)
[![ja](https://img.shields.io/badge/lang-ja-yellow.svg)](https://github.com/ohara-lab-su/image_server/blob/main/README.ja.md)

image_server is **not** a library for working with USB cameras.

This library is a **template for integrating image transfer functionality into existing programs**.
Rather than implementing OpenCV, gRPC, and a viewer from scratch each time, its goal is to enable developers to build an image transfer system quickly by modifying only the image acquisition component.

## Problems This Library Solves

Normally, the following functionality must be implemented for each project:

- Camera connection
- Frame acquisition
- JPEG compression
- Communication
- Viewer
- Connection management
- Thread management

image_server provides these functions as common components, so users only need to implement **the image acquisition component**.

## Layered Architecture

Application  
↓  
ImageStreamGrpcService  
↓  
ImageStreamCtrl  
↓  
Camera SDK

ImageStreamCtrl is the layer that abstracts the Camera SDK.
ImageStreamGrpcService is responsible solely for image streaming.

## Development Workflow

1. Run ImageStreamCtrl with OpenCV.
2. Replace OpenCV with the target SDK.
3. Start `run_image_server.py`.
4. Verify operation with the viewer.
5. Integrate it with DeviceProxy or an AI system.

## Intended Use Cases

- USB Camera
- Basler
- IDS
- HikVision
- GigE Vision
- ORiN Camera
- AI inference servers
- Visual inspection
- Robot vision
