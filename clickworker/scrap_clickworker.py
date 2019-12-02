# -*- coding: utf-8 -*-

import os
import sys
import json
import subprocess
from time import sleep
from pathlib import Path
from random import random
from datetime import datetime, date, timezone, timedelta
from time import time

# need to pip install
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def initializeDriver():

    tz_jst = timezone(timedelta(hours=9))

    print('START: {}'.format(datetime.now(tz_jst).isoformat(timespec='seconds')))
    # set virtual display via Xvfb
    print('Setting virtual window ...')
    display = Display(visible=0, size=(1024, 768))
    display.start()
    print('window start!')

    # set options
    print('reading options ...')
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--user-data-dir=/server/profile')
    # options.add_argument("--profile-directory='{}'".format('Profile 2'))
    print('Options done!')

    # set webdriver
    print('Setting webDriver ...')
    driver = webdriver.Chrome('chromedriver', options=options)
    driver.set_window_size(1024, 768)  # for Virtualdisplay
    print('webDriver is ready!')

    return driver


def solveReCaptcha(driver):

    service_key = os.environ.get('SERVICE_KEY_2CAPCHA', 'default')
    google_site_key = os.environ.get('GOOGLE_SITE_KEY_CWORK', 'default')

    # iframe 中のdisplay:none を無効化してtextareaを引きずり出している
    driver.execute_script('var element=document.getElementById("g-recaptcha-response"); element.style.display="";')
    url = "http://2captcha.com/in.php?key=" + service_key + "&method=userrecaptcha&googlekey=" + google_site_key + "&pageurl=" + pageurl 

    # 上記urlを 2capchaのサーバにPOSTしている
    resp = requests.post(url) 

    # 応答待ち
    if resp.text[0:2] != 'OK': 
        quit('Service error. Error code:' + resp.text) 
    captcha_id = resp.text[3:]

    # Make a 15-20 seconds timeout then submit a HTTP GET request to our API URL: https://2captcha.com/res.php to get the result.
    sleep(10)
    fetch_url = "http://2captcha.com/res.php?key=" + service_key + "&action=get&id=" + captcha_id

    # response があるまでひたすら待つ…！
    for i in range(1, 50):
        sleep(5) # wait 5 sec.
        resp = requests.get(fetch_url)
        if resp.text[0:2] == 'OK':
            print('  fetch OK.')
            break
    # print('Google response token: ', resp.text[3:])
    captcha_code = resp.text[3:]

    return captcha_code


def loginService(pageurl, driver):

    # config from ENVIRONMENT
    username = os.environ.get('USERNAME_CWORK', 'default')
    password = os.environ.get('PASS_CWORK', 'default')

    # まずはログイン画面を読み込む
    driver.get(pageurl)
    sleep(10 * random())

    soup = BeautifulSoup(driver.page_source, 'lxml')

    # input にusername, passwordを入力する
    if soup.find(name='input', id='username'):
        driver.find_element_by_id('username').send_keys(username)
        sleep(10 * random())
    
    if soup.find(name='input', id='password'):
        driver.find_element_by_id('password').send_keys(password)
        sleep(10 * random())
    
    if soup.find(name='textarea', id='g-recaptcha-response'):
        # textareaにトークンを入力する →　送信する
        captcha_code = solveReCaptcha(driver)
        driver.find_element_by_id('g-recaptcha-response').send_keys(captcha_code)
        sleep(10 * random())

    if soup.find(name='input', attrs={'name': 'commit', 'type': 'submit'}):
        # login ボタンを押して送信する
        loginButton = driver.find_element_by_xpath("//input[@name='commit'][@type='submit']")
        driver.execute_script("arguments[0].click();", loginButton)
        sleep(10 * random())

    print(driver.current_url)

    return driver


def outputJSON(json_list):

    tz_jst = timezone(timedelta(hours=9))

    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_CwORK', 'jobs')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d')
    target_dir.mkdir(exist_ok=True)
    filepath = target_dir / '{}.json'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))

    # json_list が空かどうかでシステムの機能が判定できる
    if json_list:
        status = 'OK'
    else:
        status = 'failure'
    
    temp_dict = {
        'service': 'clickworker',
        'timestamp': datetime.now(tz_jst).isoformat(timespec='seconds'),
        'status': status,
        'content': json_list
    }

    with open(filepath, mode='w') as f:
        f.write(json.dumps(temp_dict, indent=4, ensure_ascii=False))


def extractJobInfo(job):
    """
    job: `bs4.element.Tag`
    return: JSONize dict
    """
    # meta-infos のかたまりを抽出しておく
    meta_info = job.find(name='div', class_='meta-infos')

    tagset = meta_info.find(name='div', class_='twocolumns').find_all('p')
    temp_list = ['remainingtasks', 'timelimit', 'deadline']
    # 内包表記で辞書を作る
    return_dict = {key:''.join([x.strip() for x in tag.text.split(':')[1:]]) for key, tag in zip(temp_list, tagset)}

    # 例外処理：時折ボーナスが含まれていることがある
    span_in_price = meta_info.find(name='div', class_='price').find(name='span')
    if span_in_price is None:
        return_dict['bonus'] = None
    else:
        span = span_in_price.extract()
        # `Bonus included!` 以外のパターンもあるかもしれない（要検証）
        return_dict['bonus'] = span.text.strip()

    # 例外処理：タスクが掲載されてすぐは文頭に「NEW」と表示される
    brandnew_in_title = job.find(name='h3').find(name='span')
    if brandnew_in_title is None:
        pass
    else:
        span = brandnew_in_title.extract()  # title(h3) 内の`span` タグを除去

    # 辞書に追記していく
    return_dict['title'] = job.find(name='h3').text.strip()
    return_dict['id'] = job['id']
    return_dict['short-instruction'] = job.find(name='p', class_='short-instruction').text.strip()
    return_dict['price'] = meta_info.find(name='div', class_='price').text.strip()

    return return_dict  # json.dumps(return_dict)


def parseHTML(html):
    """
    args html: str as html
    return: list of JSON
    """

    soup = BeautifulSoup(html, 'lxml')
    jobs_list = [extractJobInfo(job) for job in soup.find_all(name='div', class_='job') if 'id' in job.attrs]

    return jobs_list


def getJobsContent(driver):

    sleep(30)  # ewbdriverWaitの場合はどうなんだろう？

    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    job_tags = soup.find(name='div', id='jobs_content').find_all(name='div', class_='job')

    if job_tags:  # ... is not None
        jobs_html_list = [tag.prettify() for tag in job_tags]
        html = '<!DOCTYPE html><html><head></head><body>{}</body></html>'.format(''.join(jobs_html_list))
        pageInfo_list = parseHTML(html)
    else:
        pageInfo_list = []

    # ファイルに出力
    outputJSON(pageInfo_list)


def escapeBash(self):
    command = ["exit", "1"]
    completed_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(completed_process.stdout.decode("utf8"))
    print(completed_process.stderr.decode("utf8"))



# ここから本番 -------------------------------------------

tz_jst = timezone(timedelta(hours=9))

print('USERNAME_CWORK: {}'.format(os.environ.get('USERNAME_CWORK', 'ENV is not configured!')))
# ログイン先URL(reCAPTCHAが設置してるURL)
pageurl = 'https://workplace.clickworker.com/en/'

try:
    driver = initializeDriver()
    loginService(pageurl, driver)
    getJobsContent(driver)

    timestamp = datetime.now(tz_jst).isoformat(timespec='seconds')
    print('{} ... STATUS: complete.\n'.format(timestamp))
    driver.quit()

except Exception as e:
    print(datetime.now(tz_jst).isoformat(timespec='seconds'), file=sys.stderr)
    print('USER EXCEPTION ! : ' + e)
    driver.quit()

