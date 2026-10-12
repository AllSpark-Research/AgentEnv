FROM python:3.13-slim-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
        libgl1 \
        libglib2.0-0 \
        libxml2 \
        libxslt1.1 \
        fonts-dejavu-core \
        unzip \
    && rm -rf /var/lib/apt/lists/*

RUN pip install \
      numpy pandas openpyxl xlrd \
      pypdf pdfplumber pymupdf pdf2image pdfminer.six \
      python-docx python-pptx reportlab weasyprint markdown \
      pillow opencv-python-headless pytesseract \
      requests httpx urllib3 beautifulsoup4 lxml feedparser \
      pyyaml jsonschema jinja2 python-dateutil tqdm cryptography \
      matplotlib seaborn scipy scikit-learn \
      dulwich flask \
      akshare yfinance \
 && pip check \
 && python -c "import numpy,pandas,openpyxl,fitz,pdfplumber,pypdf,docx,pptx,PIL,cv2,bs4,lxml,yaml,matplotlib,scipy,sklearn,dulwich,reportlab,pytesseract; print('smoke-import OK')"


WORKDIR /app

RUN (command -v curl >/dev/null 2>&1 || (apt-get update && apt-get install -y curl)) \
 && _CURL_RAE="$(curl --help all 2>/dev/null | grep -q -- '--retry-all-errors' && echo '--retry-all-errors' || true)" \
 && curl -fsSL --retry 5 --retry-delay 3 $_CURL_RAE https://nodejs.org/dist/v22.20.0/node-v22.20.0-linux-x64.tar.gz -o /tmp/node.tgz \
 && mkdir -p /opt/node && tar -xzf /tmp/node.tgz -C /opt/node --strip-components=1 \
 && ln -sf /opt/node/bin/node /usr/local/bin/node \
 && ln -sf /opt/node/bin/npm /usr/local/bin/npm \
 && ln -sf /opt/node/bin/npx /usr/local/bin/npx \
 && node --version && npm -v

COPY workspace/ /app/
COPY setup.sh /tmp/task-setup.sh
RUN bash /tmp/task-setup.sh && rm /tmp/task-setup.sh
