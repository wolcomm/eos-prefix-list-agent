ARG  REGISTRY
ARG  VERSION
FROM ${REGISTRY}/ceos-lab:${VERSION}

WORKDIR /root

COPY . .

RUN echo "nameserver 9.9.9.9" > /etc/resolv.conf
RUN python3 -m ensurepip --default-pip
RUN python3 -m pip install --upgrade pip setuptools wheel
RUN python3 -m pip install --requirement packaging/requirements-test.txt
RUN python3 -m pip install --editable .
RUN cp tests/data/startup-config /mnt/flash/
