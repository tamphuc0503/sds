FROM mcr.microsoft.com/devcontainers/python:0-3.11

WORKDIR /app

RUN apt update -y
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt install build-essential libpoppler-cpp-dev pkg-config python3-dev
RUN apt-get install tesseract-ocr -y
RUN apt install -y \
        tesseract-ocr-bul tesseract-ocr-bos tesseract-ocr-ces tesseract-ocr-dan \
        tesseract-ocr-deu tesseract-ocr-ell tesseract-ocr-eng tesseract-ocr-spa \
        tesseract-ocr-est tesseract-ocr-fin tesseract-ocr-fra tesseract-ocr-hrv \
        tesseract-ocr-hun tesseract-ocr-isl tesseract-ocr-ita tesseract-ocr-lit \
        tesseract-ocr-lav tesseract-ocr-nld tesseract-ocr-nor tesseract-ocr-pol \ 
        tesseract-ocr-por tesseract-ocr-ron tesseract-ocr-slk tesseract-ocr-slv \
        tesseract-ocr-swe

RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

RUN mkdir -p ./temp