FROM jrottenberg/ffmpeg

RUN apt-get update \
  && apt-get install -y curl fuse openssl ca-certificates \
  && apt-get clean \
  && rm -rf /var/lib/apt-lists/*

ARG GOOFYS_VERSION=v0.19.0
RUN curl -o /usr/local/sbin/goofys -L \
      https://github.com/kahing/goofys/releases/download/${GOOFYS_VERSION}/goofys \
    && chmod a+x /usr/local/sbin/goofys

RUN apt-get update \
  && apt-get install -y \
       build-essential \
       cmake \
       git \
       libgtk2.0-dev \
       pkg-config \
       libavcodec-dev \
       libavformat-dev \
       libswscale-dev \
       python3-dev \
       python3-numpy \
       python3-pip \
  && apt-get clean \
  && rm -rf /var/lib/apt-lists/* \
  && pip3 install python-dateutil pytz

ARG OPENCV_VERSION=4.0.1
RUN cd /tmp \
  && curl -O -L https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.tar.gz \
  && tar xzf ${OPENCV_VERSION}.tar.gz \
  && cd opencv-${OPENCV_VERSION} \
  && mkdir build \
  && cd build \
  && cmake -D CMAKE_BUILD_TYPE=Release -D WITH_TBB=ON -D WITH_FFMPEG=ON -D PYTHON_EXECUTABLE=/usr/bin/python3 .. \
  && make -j7 \
  && make install \
  && cd / \
  && rm -rf /tmp/${OPENCV_VERSION}.tar.gz /tmp/opencv-${OPENCV_VERSION}

COPY init.sh /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/init.sh"]

CMD ["/usr/local/bin/ffmpeg"]
