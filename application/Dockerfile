FROM python:3.12.8-alpine

ENV LD_LIBRARY_PATH=/usr/lib
WORKDIR /usr/src/app

RUN apk add \
    g++ \
    cmake \
    pkgconf \
    py3-cairo-dev \
    gobject-introspection-dev

RUN pip install --no-cache-dir pipenv

#ADD Pipfile .

#RUN pipenv install --dev
#RUN  pipenv run pyinstaller main.py --name remote-assist-display-app --add-data config/templates:config/templates --onefile

#CMD ["/bin/sh"]
ENTRYPOINT ["sh", "-c", "\
  pipenv install --dev && \
  pipenv run pyinstaller main.py \
    --name remote-assist-display-app \
    --add-data config/templates:config/templates \
    --add-data dashboard/templates:dashboard/templates \
    --onefile \
"]