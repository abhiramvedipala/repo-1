# The only egress path out of the lab-internal network — a tinyproxy that
# only allows CONNECT to PyPI/npm (and the CDNs they redirect through).
# tinyproxy filters on the CONNECT target hostname, so it works for HTTPS
# without terminating TLS.
FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends tinyproxy \
    && rm -rf /var/lib/apt/lists/*
COPY tinyproxy.conf /etc/tinyproxy/tinyproxy.conf
COPY filter.list /etc/tinyproxy/filter.list
EXPOSE 8888
CMD ["tinyproxy", "-d", "-c", "/etc/tinyproxy/tinyproxy.conf"]
