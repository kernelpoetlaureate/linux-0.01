# Dockerfile for building Linux 0.01 with a historical toolchain

FROM debian:stretch

# Use Debian archive URLs for old stretch repositories
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i '/security.debian.org/d' /etc/apt/sources.list && \
    sed -i '/stretch-updates/d' /etc/apt/sources.list && \
    echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until

RUN apt-get update && \
    apt-get install -y build-essential bison flex libgmp-dev libmpfr-dev libmpc-dev texinfo python curl && \
    apt-get clean

# Install old binutils (2.9.1) and gcc (2.7.2.3)
WORKDIR /toolchain
ADD http://ftp.gnu.org/gnu/binutils/binutils-2.9.1.tar.gz .
ADD http://ftp.gnu.org/gnu/gcc/gcc-2.7.2.3.tar.gz .
RUN tar xzf binutils-2.9.1.tar.gz && \
    tar xzf gcc-2.7.2.3.tar.gz

# Build and install binutils
WORKDIR /toolchain/binutils-2.9.1
RUN curl -o config.guess http://git.savannah.gnu.org/cgit/config.git/plain/config.guess && \
    curl -o config.sub http://git.savannah.gnu.org/cgit/config.git/plain/config.sub
RUN ./configure --prefix=/usr/local && make && make install

# Build and install gcc
WORKDIR /toolchain/gcc-2.7.2.3
RUN curl -o config.guess http://git.savannah.gnu.org/cgit/config.git/plain/config.guess && \
    curl -o config.sub http://git.savannah.gnu.org/cgit/config.git/plain/config.sub
RUN ./configure --prefix=/usr/local && make LANGUAGES=c && make install

ENV PATH="/usr/local/bin:${PATH}"
WORKDIR /src

# Usage:
# docker build -t linux001-toolchain .
# docker run -it -v /mnt/c/Users/giooo/Desktop/linux-0.01:/src linux001-toolchain /bin/bash
# cd /src && make
