FROM python:3.12.8-alpine

LABEL org.opencontainers.image.source="https://github.com/michelle-avery/remote-assist-display"

ENV LD_LIBRARY_PATH=/usr/lib
WORKDIR /usr/src/app

RUN apk add \
    g++ \
    cmake \
    pkgconf \
    py3-cairo-dev \
    gobject-introspection-dev \
    webkit2gtk-4.1-dev

RUN pip install --no-cache-dir pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --dev

ENTRYPOINT ["sh", "-c", "\
  pipenv install --dev && \
  pipenv run pyinstaller main.py \
    --name remote-assist-display-app-alpine-arm64 \
    --add-data remote_assist_display/templates:remote_assist_display/templates \
    --onefile \
"]