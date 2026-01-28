import os
import time

import zmq
import cv2

HOST = "127.0.0.1"
PORT = 65381
DELAY = 0.5

# Set up the context and REQ socket
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f"tcp://{HOST}:{PORT}")  # Connect to server

def send_image(image_path):
    # Read the image (ensure you have an image file available)
    image = cv2.imread(image_path)
    
    if image is None:
        print(f"Error: Failed to load image from {image_path}")
        return None

    # Serialize the image (convert to bytes)
    _, img_encoded = cv2.imencode('.jpg', image)
    image_data = img_encoded.tobytes()

    # Send the image to the server
    socket.send(image_data)

    # Receive the dictionary response from the server
    response = socket.recv_json()

    return response

if __name__ == "__main__":

    # Read the image (ensure you have an image file available)
    image_path_1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_img_1.jpg"))
    image_path_2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_img_2.jpg"))

    print("Image Path 1:", image_path_1)
    print("Image Path 2:", image_path_2)

    response_1 = send_image(image_path_1)
    print("Response for Image 1:", response_1)

    response_2 = send_image(image_path_2)
    print("Response for Image 2:", response_2)