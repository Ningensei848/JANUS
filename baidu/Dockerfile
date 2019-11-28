FROM ningensei848/scrap:base
WORKDIR /server

# reboot_config.sh とstart_server.shは中身が同じ
# 置く場所によって起動タイミングが異なる
# COPY ./reboot_config.sh /server/start_server.sh
# COPY ./cron_job.sh /server/cron_job.sh

# .py
COPY ./scrap_baidu.py /server/scrap.py

# permission (要検討：755 でいいのか？セキュリティ)
RUN chmod 755 /server/*

# cronの処理スクリプトを実行可能にする
RUN chmod 755 /etc/cron.d

# ubuntu 再起動時に実行するコマンドを`/etc/rc.local`においておく(最初の起動時と共通スクリプト)
# COPY ./reboot_config.sh /etc/rc.local
# RUN chmod 755 /etc/rc.local
