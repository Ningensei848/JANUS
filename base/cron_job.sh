#!/bin/bash

cd /server

filename=$(date +%Y%m%d)
stdout="/server/log/stdout.log"
stderr="/server/log/${filename}_err.log"

python /server/scrap.py >> $stdout 2>> $stderr
