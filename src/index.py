from src.server import ZMQObjectDetectionServer

HOST = "127.0.0.1"
PORT = 65382

DETECTION_LABELS = [
    "backpack",
    "mouse",
    "vulture",
    "triceratops"
]

def main(port):
    server = ZMQObjectDetectionServer(
        host=HOST,
        port=port if port is not None else PORT,
        detection_labels=DETECTION_LABELS
    )
    server.start()

if __name__ == "__main__":
    main(PORT)