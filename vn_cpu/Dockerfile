# VN-CPU Development Environment (v0.4) - Lean Edition
# Using GGUF via llama-cpp-python for low memory footprint

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    ninja-build \
    git \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir scikit-build-core

# Install llama-cpp-python (CPU only for VPS compatibility)
RUN pip3 install --no-cache-dir \
    numpy \
    pydantic \
    requests \
    llama-cpp-python \
    transformers

WORKDIR /app/vn-cpu

CMD ["/bin/bash"]
