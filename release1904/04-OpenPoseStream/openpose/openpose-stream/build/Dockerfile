FROM nvidia/cuda:8.0-cudnn6-devel-ubuntu16.04

RUN apt-get update \
    && env DEBIAN_FRONTEND=noninteractive apt-get install -y \
        build-essential \
        cmake \
        libatlas-base-dev \
        git \
        vim \
        python-dev \
        python-pip \
        python-numpy \
        libopencv-dev \
        python-opencv \
        wget \
        sudo \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG OPENPOSE_DIR=/root/openpose
ARG OPENPOSE_REPOSITORY_URL=https://github.com/CMU-Perceptual-Computing-Lab/openpose.git

ARG CUDA_ARCH_BIN=5.2
RUN cd `dirname ${OPENPOSE_DIR}` \
  && git clone ${OPENPOSE_REPOSITORY_URL} \
  && cd ${OPENPOSE_DIR} \
  && git submodule update --init --recursive \
  && bash -c " \
    cd ${OPENPOSE_DIR}; \
    export DEBIAN_FRONTEND=noninteractive; \
    export WITH_PYTHON=true NAME='U16-python-cmake-cuda8' TRAVIS_OS_NAME=linux; \
    export WITH_CUDA=false; \
    scripts/travis/install_deps_ubuntu.sh; \
    export WITH_CUDA=true; \
    sed -i -e '/-DCUDA_ARCH_BIN/s/52/${CUDA_ARCH_BIN}/' -e '/python/s/python2\.7/python3.5/' \
      -e '/libpython/s/libpython2\.7m/libpython3.5m/' scripts/travis/configure_cmake.sh; \
    bash scripts/travis/configure.sh; \
    bash scripts/travis/run_make.sh; \
    cd models; \
    ./getModels.sh; \
  "

ENV PYTHONPATH ${OPENPOSE_DIR}/build/python
WORKDIR ${OPENPOSE_DIR}

RUN apt-get update \
  && apt-get install -y curl openssl ca-certificates \
  && apt-get clean \
  && rm -rf /var/lib/apt-lists/* \
  && pip3 install kafka-python
