## ファイル構成

* 00-Kafka/
  - 00-001-ノードの起動.ipynb
  - 00-002-既存ノードの登録.ipynb
  - 00-101-Apache Kafkaのセットアップ.ipynb
  - 00-111-Kafka Connectのセットアップ.ipynb
  - 00-112-S3コネクタの登録.ipynb
  - 00-901-ノードを削除する.ipynb
* 01-raspi/
  - readme.md
  - Dockerfile
  - mss-ras.py
  - sample.ipynb
  - startup.sh
* 02-JupyterNotebook画像出力/
  - animation_consumer-tokushima_camera.ipynb
  - KafkaVideoViewer.py
* 03-YOLOStream/
  - README.txt
  - realtime_demo.py
  - kafka_consumer_wrapper.py
* 04-OpenPose stream/
  - 04-001-GPUインスタンスを起動する.ipynb
  - 04-101-OpenPoseでkafkaの画像を処理する.ipynb
  - 04-901-GPUインスタンスを削除する.ipynb
  - openpose/openpose-stream/
    + OpenPoseで処理を行うコンテナイメージ(Dockerfile)など
* 05-OpenPose offline/
  - 05-001-GPUインスタンスを起動する.ipynb
  - 05-101-OpenPoseでS3の画像を処理する.ipynb
  - 05-901-GPUインスタンスを削除する.ipynb
  - openpose/openpose-offline/
    + OpenPoseで処理を行うDockerfileなど
  - ffmpeg/
    + OpenPoseで処理した画像から動画を生成するためのDockerfileなど
* 06-Producer/
  - 06-101-動画から画像を切り出してKafkaに送る.ipynb
  - scripts/image-sender
* README.md
* LICENSE.txt
