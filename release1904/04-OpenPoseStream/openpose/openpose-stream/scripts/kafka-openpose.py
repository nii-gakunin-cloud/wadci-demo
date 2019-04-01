#!/usr/bin/python3
# -*- coding: utf-8 -*-

from logging import getLogger
from multiprocessing import Process, Queue, Array
import signal
import argparse
from kafka import (
        KafkaProducer, KafkaConsumer, TopicPartition, OffsetAndMetadata,
)
import cv2
import numpy as np
import logging.config
import os
from pathlib import Path


QUEUE_SIZE = 10

log_conf = Path('logging.conf')
if log_conf.exists():
    logging.config.fileConfig(str(log_conf))
logger = getLogger(__name__)


class OpExit(RuntimeError):
    pass


class OpProcess(Process):
    def __init__(self, setup=None, teardown=None,
                 sigs=[signal.SIGINT, signal.SIGTERM], **kw):
        super().__init__(**kw)
        self._setup = setup
        self._teardown = teardown
        self._sigs = sigs

    def run(self):
        if self._setup:
            self._kwargs['_setup'] = self._setup(*self._args, **self._kwargs)
        if self._teardown:
            def _handler(signum, frame):
                self._teardown(*self._args, **self._kwargs)
            for sig in self._sigs:
                signal.signal(sig, _handler)
        if self._target:
            try:
                self._target(*self._args, **self._kwargs)
            except OpExit:
                pass


def setup_kafka_reader(q, positions):
    cons = KafkaConsumer(
                bootstrap_servers=bootstrap_servers, group_id=group_id)
    tps = [
        TopicPartition(topic_src, x)
        for x in sorted(cons.partitions_for_topic(topic_src))
    ]

    def _usr1_handler(signum, frame):
        for tp in tps:
            cons.seek_to_end(tp)
    signal.signal(signal.SIGUSR1, _usr1_handler)
    return {'consumer': cons, 'topics': tps, }


def teardown_kafka_reader(q, positions, _setup=None):
    q.cancel_join_thread()
    cons = _setup['consumer']
    offsets = dict([
        (tp, OffsetAndMetadata(offset=positions[tp.partition], metadata=''))
        for tp in cons.assignment()
    ])
    cons.commit(offsets)
    cons.close(autocommit=False)
    logger.info("exit kafka reader process")
    raise OpExit("exit kafka reader process")


def kafka_reader(q, positions, _setup=None):
    cons = _setup['consumer']
    tps = _setup['topics']
    cons.assign(tps)
    if seek_begin:
        for tp in tps:
            cons.seek_to_beginning(tp)
    if seek_end:
        for tp in tps:
            cons.seek_to_end(tp)
    for msg in cons:
        if decimation > 1 and (msg.offset % decimation) != 0:
            logger.debug("SKIP: offset={}".format(msg.offset))
            continue
        q.put(msg)
        logger.debug("PUT0: {}: {}".format(q.qsize(), msg.offset))


def setup_kafka_writer(q, positions):
    prod = KafkaProducer(bootstrap_servers=bootstrap_servers, linger_ms=1)
    return {'producer': prod}


def teardown_kafka_writer(q, positions, _setup=None):
    q.cancel_join_thread()
    prod = _setup['producer']
    prod.close()
    logger.info("exit kafka writer process")
    raise OpExit("exit kafka writer process")


def kafka_writer(q, positions, _setup=None):
    prod = _setup['producer']
    while True:
        partition, offset, img = q.get()
        logger.debug("GET2: {} {}".format(q.qsize(), offset))

        f = prod.send(topic_dst, img.tobytes(), partition=partition)

        def update_offset(metadata):
            positions[partition] = offset
        f.add_callback(update_offset)


def setup_openpose(inq, outq):
    from openpose import pyopenpose as op

    params = {'model_folder': model_folder}
    params['body'] = body
    if hand:
        params['hand'] = True
        params['hand_detector'] = hand_detector
    if face:
        params['face'] = True
        params['face_detector'] = face_detector

    opWrapper = op.WrapperPython()
    opWrapper.configure(params)
    opWrapper.start()
    return {'opWrapper': opWrapper}


def teardown_openpose(inq, outq, _setup=None):
    inq.cancel_join_thread()
    outq.cancel_join_thread()
    opWrapper = _setup['opWrapper']
    opWrapper.stop()
    logger.info("exit openpose process")
    raise OpExit("exit openpose process")


def process_openpose(opWrapper, msg):
    from openpose import pyopenpose as op
    try:
        datum = op.Datum()
        img_ary = np.asarray(bytearray(msg.value), dtype=np.uint8)
        img = cv2.imdecode(img_ary, -1)
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        datum.cvInputData = img
        opWrapper.emplaceAndPop([datum])
        out_img = datum.cvOutputData
        ret, out_img = cv2.imencode('.jpg', out_img)
        return out_img
    except OpExit:
        raise
    except Exception as e:
        logger.exception("openpose", e)


def openpose(inq, outq, _setup=None):
    opWrapper = _setup['opWrapper']
    while True:
        msg = inq.get()
        logger.debug("GET1: {}".format(inq.qsize()))

        img = process_openpose(opWrapper, msg)

        outq.put((msg.partition, msg.offset, img))
        logger.debug("PUT1: {}".format(outq.qsize()))


def get_current_offsets():
    cons = KafkaConsumer(bootstrap_servers=bootstrap_servers)
    tps = [
        TopicPartition(topic_src, x)
        for x in sorted(cons.partitions_for_topic(topic_src))
    ]
    cons.assign(tps)
    ret = [cons.position(tp) for tp in tps]
    cons.close(autocommit=False)
    return ret


def main():
    inq = Queue(QUEUE_SIZE)
    outq = Queue(QUEUE_SIZE)
    positions = Array('i', get_current_offsets())

    def _handler(signum, frame):
        inq.close()
        outq.close()

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, _handler)

    procs = []
    procs.append(OpProcess(
        target=kafka_reader, args=(inq, positions),
        setup=setup_kafka_reader, teardown=teardown_kafka_reader,
    ))
    procs.append(OpProcess(
        target=openpose, args=(inq, outq),
        setup=setup_openpose, teardown=teardown_openpose,
    ))
    procs.append(OpProcess(
        target=kafka_writer, args=(outq, positions),
        setup=setup_kafka_writer, teardown=teardown_kafka_writer,
    ))
    for p in procs:
        p.start()

    def _usr1_handler(signum, frame):
        os.kill(procs[0].pid, signal.SIGUSR1)

    signal.signal(signal.SIGUSR1, _usr1_handler)

    for p in procs:
        p.join()


def parse_args():
    global bootstrap_servers
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--src', default='distributed-video1', dest='topic_src')
    parser.add_argument(
        '-d', '--dest', default='distributed-video1-openpose',
        dest='topic_dst')
    parser.add_argument(
        '-c', '--consumer', default='openpose-000', dest='group_id')
    parser.add_argument(
        '-b', '--brokers', default='kafka0:9092,kafka1:9092,kafka2:9092')
    parser.add_argument('-D', '--decimation', type=int, default=-1)
    parser.add_argument(
        '-m', '--model-folder', default='/root/openpose/models')
    parser.add_argument(
        '--begin', action='store_const', const=True, default=False,
        dest='seek_begin')
    parser.add_argument(
        '--end', action='store_const', const=True, default=False,
        dest='seek_end')
    parser.add_argument(
        '--hand', action='store_const', const=True, default=False)
    parser.add_argument('--hand-detector', type=int, default=2)
    parser.add_argument(
        '--face', action='store_const', const=True, default=False)
    parser.add_argument('--face-detector', type=int, default=2)
    parser.add_argument('--body', type=int, default=1)

    globals().update(vars(parser.parse_args()))
    bootstrap_servers = brokers.split(',')

if __name__ == '__main__':
    parse_args()
    main()
