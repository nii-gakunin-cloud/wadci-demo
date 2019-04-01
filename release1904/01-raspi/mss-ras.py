# RaspberryPi+カメラモジュールから
# USB接続したモバイルルータ経由で
# kafkaに画像を送り続ける
# プログラム本体

import io
import time
import argparse
import picamera
from kafka import KafkaProducer

parser = argparse.ArgumentParser()
parser.add_argument('topic')
parser.add_argument('servers', nargs='*')
args = parser.parse_args()

# kafkaに送信するためのproducerを生成する
producer = KafkaProducer(bootstrap_servers=args.servers)

frames = 60
stream = io.BytesIO()

def kafka_send():
    frame = 0
    start = time.time()
    while True :
        if frame >= frames :
            finish = time.time()
            print('Captured %d frames at %.2ffps' % (
                frames,
                frames / (finish - start)))
            frame = 0
            start = time.time()
        yield stream
# kafkaにデータを送信する
# 送信先トピックを第1引数に、画像のバイナリデータを第2引数に指定する
        producer.send(args.topic, stream.getvalue())
# flushにより、バッチ転送にはならず即座に送信が行われる
        producer.flush()
        stream.seek(0)
        stream.truncate()
        frame += 1

with picamera.PiCamera(resolution=(320,240), framerate=5) as camera:
    time.sleep(2)
    camera.capture_sequence(kafka_send(), use_video_port=True)
