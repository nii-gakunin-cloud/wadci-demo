FROM balenalib/rpi-raspbian

COPY mss-ras.py /root
COPY startup.sh /root

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y net-tools python3 python3-pip libraspberrypi-bin && \
    pip3 install kafka-python picamera

ENTRYPOINT ["/root/startup.sh"]
CMD ["distributed-video1", "kafka0:9092", "kafka1:9092", "kafka2:9092"]
