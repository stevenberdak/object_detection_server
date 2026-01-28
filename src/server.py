import atexit

from datetime import datetime

import zmq
import numpy as np
import cv2
import tensorflow as tf

from PIL import Image

from keras.applications.efficientnet import (
    EfficientNetB0 as EfficientNet,
    preprocess_input,
    decode_predictions,
)

class ZMQObjectDetectionServer:

    def __init__(
            self,
            host: str,
            port: int,
            top_k: int = 1000,
            detection_labels: list = None
        ):
        # Set up the context and REP socket
        atexit.register(self.cleanup, host, port)

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f"tcp://{host}:{port}")

        # Load EfficientNet model

        gpu_devices = tf.config.list_physical_devices("GPU")

        if gpu_devices:
            print("\nFound GPU devices:")

            for i, gpu in enumerate(gpu_devices):
                print(f"  Device {i}: {gpu.name}")
        else:
            print("\nNo GPU devices...")

        self.model = EfficientNet(weights="imagenet", )

        self.top_k = top_k
        self.detection_labels = detection_labels

        print(f"\nServer started @ {datetime.now().strftime('%H:%M:%S')}, uri = tcp://{host}:{port}")

    def cleanup(self, host, port):
        print("\nWARN: Unbinding socket, do not force close process while this completes!")
        self.socket.unbind(f"tcp://{host}:{port}")
        self.socket.close()

    def start(self):

        print("\nAwaiting incoming requests...\n(Note: First inference may take longer due to initialization of the neural net)")

        while True:
            # try:
                # Wait for the image (in byte form) from the client
                image_data = self.socket.recv()

                print(f"\nReceived image data @ {datetime.now().strftime('%H:%M:%S')}")

                # Deserialize the image (convert from byte data to an OpenCV image)
                recevied_arr = np.frombuffer(image_data, np.uint8)
                received_img = cv2.imdecode(recevied_arr, cv2.IMREAD_COLOR)

                ## ML Inference ##

                # Resize image for EfficientNet
                prepared_img = cv2.resize(
                    received_img, 
                    (self.model.input_shape[1], self.model.input_shape[2])
                )

                # Convert to np array
                prepared_arr = np.asarray(prepared_img, dtype=np.float32)
                prepared_arr = np.expand_dims(prepared_arr, axis=0)
                prepared_arr = preprocess_input(prepared_arr)

                # Inference
                model_results = self.model.predict(prepared_arr, verbose=0)
                decoded = decode_predictions(model_results, top=self.top_k)[0]

                print("\nTop results: ", decoded[0:5])

                # Filter model results based on detection labels
                filtered = np.array(list(
                    filter(
                        lambda x: x[1] in self.detection_labels,
                        decoded
                    )
                ))

                print("\nFiltered results: ", filtered)

                if len(filtered) > 0:
                    idx = np.argmax(filtered[:, 2].astype(np.float32))
                    top_label = filtered[idx][1]
                    top_score = float(filtered[idx][2])
                else:
                    top_label = None
                    top_score = None

                print("\nTop result:", top_label)
                print("\nTop score:", top_score)

                # Build response payload
                payload = {
                    "detection_labels": self.detection_labels,
                    "top_k": self.top_k,
                    "total_results": len(decoded),
                    "filtered_results": len(filtered),
                    "top_label": top_label,
                    "top_score": top_score, 
                    "results": [
                            {
                                "imagenet_id": str(imagenet_id),
                                "label": str(label),
                                "score": float(score),
                            } for (imagenet_id, label, score) in filtered
                        ]
                }
                print("\nPayload:", payload)


                print(f"\nSending response @ {datetime.now().strftime('%H:%M:%S')}")

                # Send a dictionary back to the client
                self.socket.send_json(payload)
            # except Exception as e:
            #     print("Error during request handling: ", str(e))