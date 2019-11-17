#!/bin/bash

cd /server

filename=$(date +%Y%m%d)
stdout="/var/log/stdout.log"
stderr="/var/log/${filename}_err.log"

python /server/scrap.py >> $stdout 2>> $stderr
