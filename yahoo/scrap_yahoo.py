# -*- coding: utf-8 -*-

import re
import os
import json
import subprocess
from time import sleep
from pathlib import Path
from random import random
from datetime import datetime, date, timezone, timedelta

# need to pip install
import requests
from bs4 import BeautifulSoup


def escapeBash(self):
    command = ["exit", "1"]
    completed_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(completed_process.stdout.decode("utf8"))
    print(completed_process.stderr.decode("utf8"))

def getEasyTaskList(rootURL):

    easytaskURL_list = []

    for i in range(1, 100):
        url = rootURL + str(i)
        result_set = BeautifulSoup(requests.get(url).text, 'lxml').find_all('a', class_='d_detailLink')

        easytaskURL_list += [a.attrs['href'] for a in result_set]
        
        if len(result_set) == 0:
            break
            
    return easytaskURL_list

def extractTaskInfo(soup):

    yahoo_dict = {
        'status': soup.find('div', class_='taskTitle').th.text,
        'title': soup.find('div', class_='taskTitle').h1.text,
        'entrytype': soup.find('dd', class_='entrytype').span.text,
        # 'requirements': [x.text for x in soup.find('dt', text='応募条件').parent.find_all('span')],
        'category': soup.find('ul', class_='category').text.strip(),
        'reward': soup.find('dd', class_='pt').text,
        'tasktime': soup.find('dd', class_='tasktime').text,
        'remainingtasks': soup.find('dd', class_='cnt').span.attrs['title'],
        'totaltasks': soup.find('p', text=re.compile('（全[\d,]+件）')).text,
        'activeuser': soup.find('span', id='d_workTaskNum').attrs['title'],
        'completion_rate': soup.find('span', id='d_meter').text,
        'quota_limit': soup.find('dt', class_='task').parent.dd.text,  # 一人あたりのタスク割り当て上限
        'timelimit': soup.find('dt', class_='time').parent.dd.text,
        'deadline': soup.find('dd', class_='daytime').text,
        'days_left': soup.find('dd', class_='daytime').parent.dd.text,
        'owner': soup.find('dt', class_='owner').parent.div.text,
        'task_detail': soup.find('p', class_='requestDetail').prettify()
    }

    try:
        requirement_list = [x.text for x in soup.find('dt', text='応募条件').parent.find_all('span')]
        if len(requirement_list) == 1:
            yahoo_dict['requirements'] = requirement_list[0]
        else:
            yahoo_dict['requirements'] = requirement_list
    except AttributeError as ae:
        yahoo_dict['requirements'] = []

    return yahoo_dict

def outputJSON(json_list):

    tz_jst = timezone(timedelta(hours=9))

    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_YAHOO', 'easytasks')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d')
    target_dir.mkdir(exist_ok=True)
    filepath = target_dir / '{}.json'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))

    # json_list が空かどうかでシステムの機能が判定できる
    if json_list:
        status = 'OK'
    else:
        status = 'failure'
    
    temp_dict = {
        'service': 'yahoocrowdsourcing',
        'timestamp': datetime.now(tz_jst).isoformat(timespec='seconds'),
        'status': status,
        'content': json_list
    }

    with open(filepath, mode='w') as f:
        f.write(json.dumps(temp_dict, indent=4, ensure_ascii=False))
 
def getJobsContent(rootURL):

    easytaskURL_list = getEasyTaskList(rootURL)

    easytask_list = []

    for url in easytaskURL_list:
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')
        task_id = Path(url).stem

        temp_dict = extractTaskInfo(soup)
        temp_dict['id'] = task_id
        easytask_list.append(temp_dict)
        
        # 一応、攻撃認定を避けるため間隔を空ける
        sleep(10 * random())
        continue

    outputJSON(easytask_list)

# ここから本番 -------------------------------------------

# log stdout
tz_jst = timezone(timedelta(hours=9))

try:
    rootURL = 'https://crowdsourcing.yahoo.co.jp/request/list/open/D/'
    getJobsContent(rootURL)

    timestamp = datetime.now(tz_jst).isoformat(timespec='seconds')
    print('{} ... STATUS: complete.'.format(timestamp))

except Exception as e:
    print(datetime.now(tz_jst).isoformat(timespec='seconds'))
    print('USER EXCEPTION ! : ' + e)
    escapeBash()
