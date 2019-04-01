#!/usr/bin/python3
# -*- coding: utf-8 -*-

from logging import getLogger
from multiprocessing import Process, Queue
from pathlib import Path
from time import sleep
import signal
import argparse
import cv2
import numpy as np
from dateutil import parser as dp
from dateutil import tz
from datetime import datetime as dt
from datetime import timezone
import pytz
import logging.config


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


def teardown_file_reader(q, _setup=None):
    q.cancel_join_thread()
    logger.info("exit file reader process")
    raise OpExit("exit file reader process")


def _check_mtime(p):
    file_mtime = dt.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    return s3_start_time < file_mtime


def file_reader(q, _setup=None):
    img_dir = Path(src_path)
    count = 0
    skip_count = 0
    for img_path in img_dir.glob('**/*.jpg'):
        skip_count = skip_count + 1
        if s3_start_time and not _check_mtime(img_path):
            logger.debug("SKIP datetime: {}".format(img_path))
            continue
        if skip_images > 0 and skip_count < skip_images:
            logger.debug("SKIP {}".format(img_path))
            continue

        count = count + 1
        if decimation > 1 and (count % decimation) != 0:
            logger.debug("SKIP: {}".format(img_path))
            continue

        img = cv2.imread(str(img_path))
        # _height, _width = img.shape
        # log.debug("SIZE: {}: {}".format(_width, _height))

        if img is None:
            logger.warning("not image file: {}".format(str(img_path)))
            count = count - 1
            continue
        q.put((img_path, img))
        logger.debug("PUT0: {}: {}: {}".format(count, q.qsize(), img_path))
    q.put((None, None))


def file_writer(q, width, height, rate, _setup=None):
    video = cv2.VideoWriter(dest_path, 0x21, rate, (width, height))
    count = 0
    while True:
        org_path, img = q.get()
        logger.debug("GET3: {}: {}".format(q.qsize(), count))
        if org_path is None:
            break

        img = cv2.resize(img, (width, height))
        video.write(img)

        if max_images > 0 and count >= max_images:
            logger.debug("END: The upper limit has been reached.")
            break
        count = count + 1
    video.release()


def teardown_file_writer(q, width, height, rate, _setup=None):
    q.cancel_join_thread()
    logger.info("exit file writer process")
    raise OpExit("exit file writer process")


def main():
    inq = Queue(QUEUE_SIZE)

    def _handler(signum, frame):
        inq.close()

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, _handler)

    procs = []
    procs.append(OpProcess(
        target=file_reader, args=(inq, ),
        teardown=teardown_file_reader,
    ))
    procs.append(OpProcess(
        target=file_writer, args=(inq, video_width, video_height, frame_rate),
        teardown=teardown_file_writer,
    ))

    for p in procs:
        p.start()
    procs[-1].join()
    procs[0].terminate()
    procs[0].join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--src', required=True, dest='src_path')
    parser.add_argument(
        '-d', '--dest', default='/tmp/result/openpose.mp4', dest='dest_path')
    parser.add_argument('-D', '--decimation', type=int, default=-1)
    parser.add_argument('-M', '--max-images', type=int, default=-1)
    parser.add_argument('-T', '--start-time')
    parser.add_argument('-S', '--skip-images', type=int, default=0)
    parser.add_argument('-R', '--frame-rate', type=float, default=10.0)
    parser.add_argument(
        '-H', '--height', type=int, default=200, dest='video_height')
    parser.add_argument(
        '-W', '--width', type=int, default=320, dest='video_width')

    globals().update(vars(parser.parse_args()))
    s3_start_time = None
    tzinfos = {"JST": tz.gettz("Asia/Tokyo")}
    if start_time is not None:
        x = dp.parse(start_time, tzinfos=tzinfos)
        if x.tzinfo is None or x.tzinfo.utcoffset(x) is None:
            x = pytz.timezone('Asia/Tokyo').localize(x)
        s3_start_time = x

    main()
