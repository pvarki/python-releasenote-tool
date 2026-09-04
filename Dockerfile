FROM node:22-bookworm-slim AS production

ARG MARP_VERSION=4.5.0
ARG GH_VERSION=2.98.0
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
        python3 \
        python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${TARGETARCH}.tar.gz" \
        | tar -xz -C /tmp \
    && install "/tmp/gh_${GH_VERSION}_linux_${TARGETARCH}/bin/gh" /usr/local/bin/gh \
    && rm -rf "/tmp/gh_${GH_VERSION}_linux_${TARGETARCH}"

RUN npm install -g "@marp-team/marp-cli@${MARP_VERSION}" \
    && npm cache clean --force

COPY pyproject.toml /tmp/tool/
COPY src /tmp/tool/src
RUN pip install --no-cache-dir --break-system-packages /tmp/tool \
    && rm -rf /tmp/tool

RUN git config --system --add safe.directory '*'

ENV CHROME_PATH=/usr/bin/chromium
ENV HOME=/tmp

WORKDIR /workspace
USER node
ENTRYPOINT ["releasenote"]
