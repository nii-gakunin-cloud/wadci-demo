#!/usr/bin/env python
from kafka import KafkaConsumer
import cv2
import tempfile


class KafkaConsumerWrapper:
    # kafkaConsumerのトピックとサーバを設定
    # Setting of topic and servers in kafkaConsumer
    def __init__(self, topic, server):
        self.consumer_iter = KafkaConsumer(topic, bootstrap_servers=server).__iter__()
        self.nexts = []


    def isOpened(self):
        if self.nexts:
            return True
        try:
            self.nexts.append(next(self.consumer_iter))
            return True
        except StopIteration:
            return False

    # フレームを読み込み
    # Read of frame
    def read(self):
        dat = None
        if self.nexts:
            dat = self.nexts.pop(0)
        else:
            try:
                dat = next(self.consumer_iter)
            except StopIteration:
                return False, None
        assert dat is not None
        # with tempfile.TemporaryFile('wb') as f:
        with open('___', 'wb') as f:
            f.write(dat.value)
            f.flush()
            return True, cv2.imread(f.name)


if __name__ == '__main__':
    cap = KafkaConsumerWrapper('distributed-video1', 'hogehoge:9092')
    assert cap.isOpened(), 'Cannot capture source'

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            pass
        else:
            break

