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
from openpose import pyopenpose as op


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


def get_done_file():
    done_path = Path(dest_path) / '.done'
    if done_path.exists():
        with done_path.open() as f:
            return f.read()
    else:
        return ''


def _check_mtime(p):
    file_mtime = dt.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
    return s3_start_time < file_mtime


def file_reader(q, _setup=None):
    done_fname = get_done_file()
    img_dir = Path(src_path)
    count = 0
    # for img_path in sorted(img_dir.glob('**/*.bin')):
    for img_path in img_dir.glob('**/*.bin'):
        if img_path.name < done_fname:
            logger.debug("SKIP: {}".format(img_path))
            continue
        if s3_start_time and not _check_mtime(img_path):
            logger.debug("SKIP datetime: {}".format(img_path))
            continue

        count = count + 1
        if decimation > 1 and (count % decimation) != 0:
            logger.debug("SKIP: {}".format(img_path))
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            logger.warning("not image file: {}".format(str(img_path)))
            count = count - 1
            continue
        q.put((img_path, img))
        logger.debug("PUT0: {}: {}: {}".format(count, q.qsize(), img_path))


def file_writer(q, _setup=None):
    result_dir = Path(dest_path)
    src_dir = Path(src_path)
    result_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    while True:
        org_path, img = q.get()
        logger.debug("GET3: {}: {}".format(q.qsize(), count))

        img_path = result_dir / org_path.relative_to(
                        src_dir).with_suffix('.jpg')
        cv2.imwrite(str(img_path), img)
        with (result_dir / '.done').open(mode='w') as f:
            f.write(org_path.name)

        if max_images > 0 and count >= max_images:
            logger.debug("END: The upper limit has been reached.")
            break
        count = count + 1


def teardown_file_writer(q, _setup=None):
    q.cancel_join_thread()
    logger.info("exit file writer process")
    raise OpExit("exit file writer process")


def setup_openpose(inq, out0q):
    gpus = op.get_gpu_number()
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
    return {'opWrapper': opWrapper, 'gpus': gpus}


def teardown_openpose(inq, out0q, _setup=None):
    inq.cancel_join_thread()
    out0q.cancel_join_thread()
    opWrapper = _setup['opWrapper']
    opWrapper.stop()
    logger.info("exit openpose process")
    raise OpExit("exit openpose process")


def process_openpose(opWrapper, images):
    try:
        datums = []
        for img in images:
            datum = op.Datum()
            datum.cvInputData = img['image']
            datums.append(datum)

        for datum in datums:
            opWrapper.waitAndEmplace([datum])

        result = []
        for idx, datum in enumerate(datums):
            opWrapper.waitAndPop([datum])
            out_img = datum.cvOutputData
            logger.debug("IMAGE: {}".format(len(out_img)))
            result.append({'image': out_img, 'path': images[idx]['path']})

        return result
    except OpExit:
        raise
    except Exception as e:
        logger.exception("openpose", e)


def _openpose(inq, out0q, opWrapper, gpus):
    while True:
        images = []
        for gpu in range(gpus):
            img_path, img = inq.get()
            logger.debug("GET1: {}: {}".format(inq.qsize(), img_path))
            images.append({'path': img_path, 'image': img})

        for img in process_openpose(opWrapper, images):
            img_path = img['path']
            out0q.put((img_path, img['image']))
            logger.debug("PUT1a: {}: {}".format(out0q.qsize(), img_path))


def openpose(inq, out0q, _setup=None):
    opWrapper = _setup['opWrapper']
    gpus = _setup['gpus']
    try:
        _openpose(inq, out0q, opWrapper, gpus)
    except OSError as e:
        logger.debug("openpose: " + str(e))


def main():
    inq = Queue(QUEUE_SIZE)
    out0q = Queue(QUEUE_SIZE)

    def _handler(signum, frame):
        inq.close()
        out0q.close()

    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, _handler)

    procs0 = []
    procs0.append(OpProcess(
        target=file_reader, args=(inq, ),
        teardown=teardown_file_reader,
    ))
    procs0.append(OpProcess(
        target=file_writer, args=(out0q, ),
        teardown=teardown_file_writer,
    ))
    procs1 = []
    procs1.append(OpProcess(
        target=openpose, args=(inq, out0q),
        setup=setup_openpose, teardown=teardown_openpose,
    ))

    for p in procs0 + procs1:
        p.start()

    procs = procs1
    while True:
        for p in procs0:
            p.join(0.1)
            if p.exitcode is not None:
                procs = list(set(procs0) - set([p])) + procs1
                break
        else:
            continue
        break

    for p in procs:
        p.terminate()
    for p in procs:
        p.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--src', required=True, dest='src_path')
    parser.add_argument('-d', '--dest', required=True, dest='dest_path')
    parser.add_argument('-D', '--decimation', type=int, default=-1)
    parser.add_argument('-M', '--max-images', type=int, default=-1)
    parser.add_argument('-T', '--start-time')
    parser.add_argument(
        '-m', '--model-folder', default='/root/openpose/models')
    parser.add_argument(
        '--hand', action='store_const', const=True, default=False)
    parser.add_argument('--hand-detector', type=int, default=2)
    parser.add_argument(
        '--face', action='store_const', const=True, default=False)
    parser.add_argument('--face-detector', type=int, default=2)
    parser.add_argument('--body', type=int, default=1)

    globals().update(vars(parser.parse_args()))
    s3_start_time = None
    tzinfos = {"JST": tz.gettz("Asia/Tokyo")}
    if start_time is not None:
        x = dp.parse(start_time, tzinfos=tzinfos)
        if x.tzinfo is None or x.tzinfo.utcoffset(x) is None:
            x = pytz.timezone('Asia/Tokyo').localize(x)
        s3_start_time = x

    main()
