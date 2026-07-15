# save_image_sample.py

from image_stream_ctrl import ImageStreamDeviceClass


def main():
    dev = ImageStreamDeviceClass(
        camera_id=0,
        jpeg_quality=90,
    )

    try:
        payload = dev.capture_once()

        image_bytes = payload["image"]
        frame_id = payload["frame_id"]
        filename = "capture_%06d.jpg" % frame_id

        with open(filename, "wb") as f:
            f.write(image_bytes)

        print("saved:", filename)
        print("width:", payload["width"])
        print("height:", payload["height"])
        print("timestamp_ns:", payload["timestamp_ns"])

    finally:
        dev.disconnect()


if __name__ == "__main__":
    main()