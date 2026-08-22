# Reproducible CAGE-owned player-side runtime for build_target R5 replay.
# Build from the repository root:
#   docker build -f examples/build_target/serve/solver.Dockerfile \
#     -t cage/build-target-solver:2026-08-v1 .
FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

LABEL io.cage.build-target.solver-contract="pwn-python-v1"
LABEL org.opencontainers.image.title="CAGE build-target solver"

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PWNLIB_NOTERM=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        binutils \
        binutils-multiarch \
        ca-certificates \
        file \
        gcc \
        libc6-dev \
        make \
        patchelf \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --no-cache-dir \
        pwntools==4.15.0 \
        pycryptodome==3.23.0 \
        requests==2.34.2 \
    && python3 -c "import Crypto, pwn, pwnlib, requests; print(Crypto.__version__, pwnlib.__version__, requests.__version__)"

WORKDIR /solve
