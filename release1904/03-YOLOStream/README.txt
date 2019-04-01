# 03-YOLOStream パッケージ

ストリームデータに対してYOLO v3とPyTorchを用いて物体認識をするコード一式です．
AWSのGPUインスタンスを利用します．


## 準備

1. AWSのg3.4xlargeを使用します．
   インスタンス作成時に以下のAMIを指定します．
   Deep Learning AMI (Ubuntu) Version 22.0 - ami-06868a6ddab784c28
   （注意：g2インスタンスはPyTorchをサポートしていないので，使えません）

2. sshでログイン後，以下を実行して環境変数を設定します．
   $ source activate pytorch_p36

3. OSの更新とOpenCV，Kafkaライブラリのインストール
   $ sudo apt-get update; sudo apt-get upgrade
   $ pip install --upgrade pip; python -m pip install opencv-python kafka-python

4. YOLO v3関係のコードをgitでダウンロードします．
   $ git clone https://github.com/ayooshkathuria/pytorch-yolo-v3.git

5. 学習データをダウンロードします．
   $ cd pytorch-yolo-v3/ ; wget https://pjreddie.com/media/files/yolov3.weights

6. 以下のデモ用コードを pytorch-yolo-v3/ にコピーします．
   realtime_demo.py -- nii SINET realtime demo
   KafkaConsumerWrapper.py -- Kafka Consumer Wrapper

7. プログラムを実行します．
   $ python realtime_demo.py
   （注意：01-raspiまたは06-Producerで，Kafka Producerコードを動かす必要があります．）
   （注意：realtime_demo.pyの144行目，149行目あたりで，Kafkaサーバ，トピック名の設定などが必要です．）


## pytorch-yolo-v3とデモ用コードの構成
・デモ用コードの概要説明
Python File
	 realtime_demo.py -- nii SINET realtime demo
	 KafkaConsumerWrapper.py -- Kafka Consumer Wrapper

package of pytorch-yolo-v3　
- Folder
	cfg --config seeting
	imgs -- image data
	det -- detect results	
	data -- detect object name list

- Other File
  	cam_demo.py -- camera demo
	video_demo.py -- video demo
	detect.py -- image detect demo
	 
	yolov3.weights --training data
	pallete -- camera device invocation
	darknet.py --YOLO v3 Initialize         
	__init__.py  -- Pytorch Library                                
	preprocess.py -- Pytorch Library                                    
	bbox.py -- Pytorch Library                              
	util.py　-- Pytorch Library 
	README.md -- how to use command to run the demos
	（pytorch-yolo-v3の詳細な使い方はREADME.mdにかかれています．）
