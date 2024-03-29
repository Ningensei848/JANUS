#!/bin/bash

service cron start
sleep 10

# cronjob settings here!
cronjob='0,15,30,45 * * * * root /bin/bash /server/cron_job.sh'

# ~/.bashrc に変数が含まれていなかったらenvから追記する
cronfile=/etc/cron.d/crontask

if cat $cronfile | grep 'DATA_VOLUME' >/dev/null; then
    echo "ENV have been included."
else
    echo "ENV have not been included."
    echo 'SHELL=/bin/bash' > $cronfile
    for e in `env`
    do
    echo $e >> $cronfile
    done

    echo "${cronjob}" >> $cronfile

    echo "COMPLETE: ADD ENV to .bashrc ."
fi

crontab /etc/cron.d/crontask
crontab -l
