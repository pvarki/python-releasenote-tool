ARG UV_VERSION=0.9.7
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM node:22-bookworm-slim AS production

ARG MARP_VERSION=4.5.0
ARG GH_VERSION=2.98.0
ARG PYTHON_VERSION=3.14
ARG TARGETARCH

# LibreOffice required for pptx to be editable. Without it marp
# pastes a picture of each slide.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        chromium \
        curl \
        fonts-dejavu-core \
        fonts-liberation \
        fonts-noto-color-emoji \
        fonts-noto-core \
        git \
        libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${TARGETARCH}.tar.gz" \
        | tar -xz -C /tmp \
    && install "/tmp/gh_${GH_VERSION}_linux_${TARGETARCH}/bin/gh" /usr/local/bin/gh \
    && rm -rf "/tmp/gh_${GH_VERSION}_linux_${TARGETARCH}"

RUN npm install -g "@marp-team/marp-cli@${MARP_VERSION}" \
    && npm cache clean --force

COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv venv --python "${PYTHON_VERSION}" /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY pyproject.toml /tmp/tool/
COPY src /tmp/tool/src
RUN uv pip install --python /opt/venv/bin/python --no-cache /tmp/tool \
    && rm -rf /tmp/tool

RUN git config --system --add safe.directory '*'

ENV CHROME_PATH=/usr/bin/chromium
ENV HOME=/tmp

WORKDIR /workspace
USER node
ENTRYPOINT ["releasenote"]
