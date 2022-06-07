FROM kenhv/mirrorbot:ubuntu

WORKDIR /usr/src/app
COPY . .
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

RUN set -ex \
    && chmod 777 /usr/src/app \
    && cp netrc /root/.netrc \
    && cp extract pextract /usr/local/bin \
    && chmod +x aria.sh /usr/local/bin/extract /usr/local/bin/pextract

CMD ["bash", "start.sh"]
