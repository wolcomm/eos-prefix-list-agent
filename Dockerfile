ARG  REGISTRY
ARG  VERSION
FROM ${REGISTRY}/ceos-lab:${VERSION}

WORKDIR /root

COPY . .

RUN echo "nameserver 9.9.9.9" > /etc/resolv.conf
RUN pip install --upgrade pip
RUN pip install --requirement packaging/requirements-test.txt
RUN pip install --editable .
RUN cp tests/data/startup-config /mnt/flash/
