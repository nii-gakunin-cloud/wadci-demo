#!/bin/bash

# RaspberryPi+カメラモジュールから
# USB接続したモバイルルータ経由で
# kafkaに画像を送り続ける

# USB接続したモバイルルータはeth1として認識される
# デフォルトのmtuが大きくてモバイル網を通せないので1200に絞る
/sbin/ifconfig eth1 mtu 1200

# プログラム本体を呼び出す
/usr/bin/python3 /home/pi/mss-ras.py $@
