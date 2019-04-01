
# 広域データ収集基盤デモパッケージ（RaspberryPi部）

広域データ収集基盤デモパッケージにおいて、画像を撮影し基盤に送信する、RaspberryPi部分の資材一式です。

## 用意するもの

* RaspberryPi
* RaspberryPi専用カメラモジュール
* SINET-SIM入りモバイルルータ（RaspberryPiにUSB接続しeth1として認識されるもの）

## 準備

画像を撮影し基盤に送信するソフトウェアはDockerコンテナで提供されます。

https://www.raspberrypi.org/blog/docker-comes-to-raspberry-pi/

などを参考に、RaspberryPiでDockerコンテナが動くようにしてください。

また、RaspberryPi専用カメラモジュールを有効化するために、

```
sudo raspi-config nonint do_camera 0
```

を実行しておいてください。

## 使用するコンテナイメージ

https://cloud.docker.com/u/mnagaku/repository/docker/mnagaku/mss-raspi

ビルド済みのコンテナイメージを公開しているので、特に準備は不要です。

ビルドに必要な資材一式は、本パッケージに揃えてありますので、ご自身でビルドすることもできます。

## 実行

```
sudo docker run --privileged --net=host --restart=always --add-host=kafka0:192.168.2.100 --add-host=kafka1:192.168.2.101 --add-host=kafka2:192.168.2.102 mnagaku/mss-raspi
```

RaspberryPi専用カメラモジュールを使用するために「--privileged」が必要です。eth1のmtuを調整するために「--net=host」が必要です。RaspberryPi起動時に、自動的に画像送信を開始するために「--restart=always」が必要です。送信先のkafka基盤において名前解決が問題になり、かつ、DNSの支援が受けられない場合は、「--add-host」による名前解決の設定が必要です。

送信先についてのデフォルト設定は、トピック名が「distributed-video1」、サーバ指定が、「kafka0:9092」「kafka1:9092」「kafka2:9092」の3台です。

送信先についての設定は、コンテナ起動時に引数で指定することができます。

```
sudo docker run --privileged --net=host --restart=always --add-host=kafka0:192.168.2.100 --add-host=kafka1:192.168.2.101 --add-host=kafka2:192.168.2.102 mnagaku/mss-raspi distributed-video2 kafka0:9092 kafka1:9092 kafka2:9092
```

## 動作確認

本パッケージに含まれるsample.ipynbを環境に合わせて改変して動作確認を行えます。

本パッケージ作成時点で、sample.ipynbで使用しているkafka-pythonに不具合があり、メモリが分離されない環境で異なるトピックからデータを取得する複数のconsumerを動作させると、データが混信する挙動が確認されています。コンテナ払い出しをspawnerとするJupyterHubで複数アカウントを使い、メモリ環境を分離することで、対策できます。
