# Required libraries
# pip install kafka-python --user
# pip install Pillow --user
# pip install opencv-python --user
#
# $ python KafkaStreamer.py --topic <topic name> --title <frame title>

import argparse
import cv2
import io
import numpy as np
from PIL import Image
from kafka import KafkaConsumer

servers = [
    'kafka0.example.org:9092',
    'kafka1.example.org:9092',
    'kafka2.example.org:9092',
]

parser = argparse.ArgumentParser()
parser.add_argument('--topic', help='optional')
parser.add_argument('--title', help='optional')
args = parser.parse_args()

topic = 'distributed-video1'
title = topic
if args.topic:
    topic = args.topic
if args.title:
    title = args.title


consumer = KafkaConsumer(topic, bootstrap_servers=servers)

for msg in consumer:
    img = Image.open(io.BytesIO(msg.value))
    img_numpy = np.asarray(img)
    img_numpy_bgr = cv2.cvtColor(img_numpy, cv2.COLOR_RGBA2BGR)

    cv2.imshow(title, img_numpy_bgr)
    cv2.waitKey(1)
