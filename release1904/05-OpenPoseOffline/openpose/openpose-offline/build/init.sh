#!/bin/bash

: ${BUCKET:?ERROR: bucket name is not set.}
: ${MOUNT_DIR:=/mnt/s3}

mkdir -p $MOUNT_DIR
/usr/local/sbin/goofys -f \
    --region ${REGION:-ap-northeast-1} \
    --stat-cache-ttl ${STAT_CACHE_TTL:-1m0s} \
    --type-cache-ttl ${TYPE_CACHE_TTL:-1m0s} \
    --dir-mode ${DIR_MODE:-0500} \
    --file-mode ${FILE_MODE:-0600} \
    $BUCKET $MOUNT_DIR &

for i in $(seq 1 10); do
  if mount -t fuse | grep -q $MOUNT_DIR; then
    break;
  fi
  sleep 1
done

exec "$@"
