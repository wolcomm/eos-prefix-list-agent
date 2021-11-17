ARG  REGISTRY
ARG  VERSION
FROM ${REGISTRY}/ceos-lab:${VERSION}

WORKDIR /root

RUN echo "nameserver 9.9.9.9" > /etc/resolv.conf
RUN python3 -m ensurepip --default-pip
RUN python3 -m pip install --upgrade pip setuptools wheel

RUN mkdir -p tests

COPY ./requirements-test.txt ./
RUN python3 -m pip install --requirement requirements-test.txt

COPY ./startup-config /mnt/flash
