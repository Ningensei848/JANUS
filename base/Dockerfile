FROM ubuntu:18.04
LABEL maintainer="ningensei848 <k.kubokawa@klis.tsukuba.ac.jp>" \
    version="1.0"
WORKDIR /server/

# apt で取りに行くサーバを変更して速度を改善（JAISTがベストなのかは不明）
RUN sed -i 's@archive.ubuntu.com@ftp.jaist.ac.jp/pub/Linux@g' /etc/apt/sources.list


COPY ./cron_job.sh /server/cron_job.sh
COPY ./reboot_config.sh /server/start_server.sh
COPY ./requirements.txt /server/requirements.txt

# ubuntu 再起動時に実行するコマンドを`/etc/rc.local`においておく(最初の起動時と共通スクリプト)
COPY ./reboot_config.sh /etc/rc.local
RUN chmod 755 /etc/rc.local

# python3.8 のインストール

RUN apt -y update && apt install -y --no-install-recommends \
    wget git gnupg unzip cron vim systemd xvfb fonts-noto-cjk software-properties-common python3-distutils

# python3.8 のインストール
RUN add-apt-repository ppa:deadsnakes/ppa -y && apt install -y python3.8

# make some useful symlinks that are expected to exist
RUN which python3.8
RUN python3.8 --version
RUN cd /usr/bin \
	&& ln -s idle3 idle \
	&& ln -s pydoc3 pydoc \
	&& ln -s python3.8 python \
	&& ln -s python3-config python-config

RUN wget --no-check-certificate https://bootstrap.pypa.io/get-pip.py && python get-pip.py \
    && rm -f get-pip.py

# chrome をインストール  (google-chrome-stable　なのでヴァージョンがあがるかもしれない)
RUN wget --no-check-certificate https://dl.google.com/linux/linux_signing_key.pub \
    && apt-key add linux_signing_key.pub \
    && echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list \
    && : "cf. https://www.ubuntuupdates.org/package/google_chrome/stable/main/base/google-chrome-stable" \
    && apt -y update && apt install -y --no-install-recommends google-chrome-stable \
    build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev \
    libssl-dev libreadline-dev libffi-dev wget google-chrome-stable \
    && apt clean && rm -r /var/lib/apt/lists/* 

# chromedriver をインストール　（現行　78.0.3904.70：stable が上がったら変更する可能性）
RUN wget --no-check-certificate https://chromedriver.storage.googleapis.com/78.0.3904.70/chromedriver_linux64.zip \
    && unzip chromedriver_linux64.zip \
    && mv chromedriver /bin/ \
    && rm chromedriver_linux64.zip \
    && rm linux_signing_key.pub

# python ライブラリのインストール
RUN pip install -r requirements.txt \
    && rm requirements.txt
