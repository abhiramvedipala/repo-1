# codercom/code-server with Python baked in.
#
# Baked in at BUILD time (full internet access) rather than installed at
# container-start time, because sessions run on a network that only allows
# egress to PyPI/npm (see docker/squid/squid.conf) — apt.debian.org isn't
# on that allowlist, and shouldn't need to be.
FROM codercom/code-server:latest

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*
USER coder
