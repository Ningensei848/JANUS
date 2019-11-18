import os
import re
import sys
import json
import subprocess

from time import sleep
from pathlib import Path
from random import random
from multiprocessing import Process
from datetime import datetime, date, timezone, timedelta

# need to pip install
import requests
from flask import Flask, jsonify, request, Response
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import exceptions
from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ---------------------------------------------------------
def escapeBash(self):
    command = ["exit", "1"]
    completed_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(completed_process.stdout.decode("utf8"))
    print(completed_process.stderr.decode("utf8"))

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
    print('Options done!')

    # set webdriver
    print('Setting webDriver ...')
    driver = webdriver.Chrome('chromedriver', options=options)
    driver.set_window_size(1024, 768)  # for Virtualdisplay
    print('webDriver is ready!')

    return driver

# サーバとのPOST通信に使う関数（使わないかも）----------------
# flask サーバーのための魔法のコメント（2行）
app = Flask(__name__)
@app.route('/mturk',methods=["POST"])
def index():
    # JSON 以外がPOSTされたらエラーを吐く
    if request.headers['Content-Type'] != 'application/json':
        print(request.headers['Content-Type'], file=sys.stderr)
        return flask.jsonify(res='error'), 400
    # JSONがPOSTされたら...
    if request.method == 'POST':
        posted_json = json.loads(request.get_json()) # Get POSTed JSON
        otp = posted_json['OTP']
        os.environ['ONE_TIME_PASSWORD_MTURK'] = otp
    return 

@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(500)
def error_handler(error):
    response = jsonify({ 
                          "error": {
                          "type": error.name, 
                          "message": error.description 
                          }
                      })
    return response, error.code

# OAUTH: オーオースと読むらしい
def otpOAUTH(driver):
    # for multiprocess.Process
    arguments = {
        'debug': False,
        'host': '0.0.0.0',
        'port': 8765,
    }
    # app.run(debug=False, host='0.0.0.0', port=8765)
    server = Process(target=app.run, kwargs=arguments)
    server.start()
    otp = ''
    for _ in range(15):
        sleep(30)
        if os.environ['ONE_TIME_PASSWORD_MTURK']:
            otp = os.environ['ONE_TIME_PASSWORD_MTURK']
            os.environ['ONE_TIME_PASSWORD_MTURK'] = ''
            break
        continue

    server.terminate()
    server.join()  # processが完全に終了するまで待つ

    if len(otp) == 0:
        print('One Time Password has not been received!', file=sys.stderr)
        sys.exit('One Time Password has not been received!', file=sys.stderr)
        pass
    else:
        # <input type="text" maxlength="6" required="" name="code" class="a-input-text a-span12 cvf-widget-input cvf-widget-input-code">
        driver.find_element_by_xpath("//input[@type='text'][@name='code'][@maxlength='6']").send_keys(otp)
        sleep(10 * random())
        driver.execute_script("arguments[0].click();", loginButton)
        sleep(10 * random())
    
    return driver

# ---------------------------------------------------------

# debug 用の関数
def outputHTML(html):
    
    tz_jst = timezone(timedelta(hours=9))

    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_MTURK', 'hits')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d')
    target_dir.mkdir(exist_ok=True)
    filepath = target_dir / '{}.html'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))

    with open(filepath, mode='w') as f:
        f.write(html)

def login(pageurl, driver):
    # config from ENVIRONMENT
    username = os.environ.get('USERNAME_MTURK', 'default')
    password = os.environ.get('PASS_MTURK', 'default')
    service_key = os.environ.get('SERVICE_KEY_2CAPCHA', 'default')
    google_site_key = os.environ.get('GOOGLE_SITE_KEY_MTURK', 'default')

    # まずはログイン画面を読み込む
    driver.get(pageurl)
    # input にusername, passwordを入力する
    driver.find_element_by_id('ap_email').send_keys(username)
    sleep(10 * random())
    driver.find_element_by_id('ap_password').send_keys(password)
    sleep(10 * random())

    # login ボタンを押して送信する
    # loginButton = driver.find_element_by_xpath("//input[@name='commit'][@type='submit']")
    loginButton = driver.find_element_by_id('signInSubmit')
    driver.execute_script("arguments[0].click();", loginButton)
    sleep(30 * random())

    # for debug
    # print(driver.current_url)
    # outputHTML(driver.page_source)
    sleep(30 * random())

    try:
        # ワンタイムパスワードの入力画面へ進む
        driver.find_element_by_xpath('//*[text()=continue]').submit()
        sleep(30 * random())
        otpOAUTH(driver)        
    except exceptions.NoSuchElementException as nse:
        sleep(30 * random())
        print(str(nse), file=sys.stderr)

    print(driver.current_url, file=sys.stderr)

    return driver

def countPages(driver):

    # クエリからページ数とコンテンツ数を指定して対象とするページの一覧を集める
    rootURL = 'https://worker.mturk.com/?page_number=1&page_size=100'
    driver.get(rootURL)
    sleep(20 * random())
    html = driver.page_source
    sleep(10 * random())

    # data-react-class="require('reactComponents/navigation/Pagination')['default']"
    soup = BeautifulSoup(html, 'lxml')
    target = "require('reactComponents/navigation/Pagination')['default']"

    # outputHTML(html)

    tag_obj = soup.find(name='div', attrs={'data-react-class': target})  # data-react-class でオブジェクトを取得して...
    react_data = json.loads(tag_obj['data-react-props'])  # data-react-propsの属性値をとる！
    lastPage = react_data['lastPage']

    page_list = ['https://worker.mturk.com/?page_number={}&page_size=100'.format(i) for i in range(1, lastPage + 1)]

    return page_list

def outputJSON(json_dict):

    tz_jst = timezone(timedelta(hours=9))

    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_MTURK', 'hits')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d')
    target_dir.mkdir(exist_ok=True)
    filepath = target_dir / '{}.json'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))

    if len(json_dict['bodyData']) == 0:
        status = 'failure'
    else:
        status = 'OK' 

    temp_dict = {
        'service': 'AmazonMechanicalTurk',
        'timestamp': datetime.now(tz_jst).isoformat(timespec='seconds'),
        'status': status,
        'content': json_dict
    }    

    with open(filepath, mode='w') as f:
        f.write(json.dumps(temp_dict, indent=4, ensure_ascii=False))

def getHITContent(page_list):

    json_dict = {}
    json_dict['bodyData'] = []

    for url in tqdm(page_list, desc='Total {} pages: '.format(len(page_list))):

        driver.get(url)
        sleep(20 * random())
        html = driver.page_source
        sleep(10 * random())   

        soup = BeautifulSoup(html, 'lxml')
        # data-react-class="require('reactComponents/hitSetTable/HitSetTable')['default']"
        target = "require('reactComponents/hitSetTable/HitSetTable')['default']"
        tag_obj = soup.find(name='div', attrs={'data-react-class': target})  # data-react-class でオブジェクトを取得して...
        react_data = json.loads(tag_obj['data-react-props'])  # data-react-propsの属性値をとる！

        json_dict['bodyData'].extend(react_data['bodyData'])
        json_dict['tableConfig'] = react_data['tableConfig']

    return json_dict  # dict

# ここから本番 -------------------------------------------

# ログイン先URL(reCAPTCHAが設置してるURL)
pageurl = 'https://worker.mturk.com/'

# log stdout
tz_jst = timezone(timedelta(hours=9))

try:
    driver = initializeDriver()
    login(pageurl, driver)
    page_list = countPages(driver)
    json_dict = getHITContent(page_list)
    outputJSON(json_dict)

    timestamp = datetime.now(tz_jst).isoformat(timespec='seconds')
    message = 'DATA_VOLUME_MTURK: {}'.format(os.environ.get('DATA_VOLUME_MTURK', 'ENV is not configured!'))
    print(timestamp + '...' + message)

except Exception as e:
    print(datetime.now(tz_jst).isoformat(timespec='seconds'), file=sys.stderr)
    print('USER EXCEPTION ! : ' + e, file=sys.stderr)
    driver.quit()
    escapeBash()
