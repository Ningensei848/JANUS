# -*- coding: utf-8 -*-

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

def outputImage(url):
    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_MTURK', 'hits')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d') / 'img'
    target_dir.mkdir(exist_ok=True)
    filepath = target_dir / 'captchaImage.jpg'
    
    res = requests.get(url, stream=True)

    if res.status_code == 200:
        with open(filepath, 'wb') as file:
            for chunk in res.iter_content(chunk_size=1024):
                file.write(chunk)

    return filepath

def getCaptchaCode(html):
    
    # config from ENVIRONMENT
    username = os.environ.get('USERNAME_MTURK', 'default')
    password = os.environ.get('PASS_MTURK', 'default')
    service_key = os.environ.get('SERVICE_KEY_2CAPCHA', 'default')

    soup = BeautifulSoup(html, 'lxml')
    captcha_body = soup.find(name='div', id='image-captcha-section')

    # outputHTML(html, tag="confirmImg")

    instruction = captcha_body.find(name='h4').text.strip()
    imgURL = captcha_body.find(name='img', id='auth-captcha-image')['src']

    method = 'post'  # defines that you're sending an image with multipart form
    url = "http://2captcha.com/in.php?key=" + service_key + "&method={}".format(method) + "&textinstructions={}".format(instruction)
    filepath = outputImage(imgURL)
    files = {'file': open(filepath, 'rb')}
    data = {'key': service_key, 'method': 'post'}
    resp = requests.post(url, files=files, data=data) 

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
            print('\n fetch OK.\n')
            break
        else:
            print(resp.text)

    captcha_code = resp.text[3:]

    return captcha_code


def initializeDriver():

    tz_jst = timezone(timedelta(hours=9))

    print('START: {}'.format(datetime.now(tz_jst).isoformat(timespec='seconds')))
    # set virtual display via Xvfb
    # print('Setting virtual window ...')
    # display = Display(visible=0, size=(1024, 768))
    # display.start()
    # print('window start!')

    # set options
    print('reading options ...')
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('disable-infobars')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--user-data-dir={}'.format(os.environ.get('GOOGLE_PROFILE_PATH', '/server/profile')))
    options.add_argument('--user-data-dir={}'.format(os.environ.get('GOOGLE_PROFILE_PATH', r'C:\Users\kiai\AppData\Local\Google\Chrome\User Data')))
    options.add_argument("--profile-directory={}".format('Profile 1'))

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

def getOTP():
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
        if len(os.environ['ONE_TIME_PASSWORD_MTURK']):
            otp = os.environ['ONE_TIME_PASSWORD_MTURK']
            os.environ['ONE_TIME_PASSWORD_MTURK'] = ''
            server.terminate()
            server.join()  # processが完全に終了するまで待つ
            break

    if len(otp) == 0:
        print('One Time Password has not been received!', file=sys.stderr)
        sys.exit('One Time Password has not been received!', file=sys.stderr)
    
    return otp

# ---------------------------------------------------------

# debug 用の関数
def outputHTML(html, tag=""):
    
    tz_jst = timezone(timedelta(hours=9))

    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_MTURK', 'hits')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d')
    target_dir.mkdir(exist_ok=True)
    if len(tag) != 0:
        filepath = target_dir / '{}_{}.html'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'), tag)
    else:
        filepath = target_dir / '{}.html'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))

    with open(filepath, mode='w', encoding='utf-8') as f:
        f.write(html)

def login(pageurl, driver):
    # config from ENVIRONMENT
    username = os.environ.get('USERNAME_MTURK', 'default')
    password = os.environ.get('PASS_MTURK', 'default')

    # まずはログイン画面を読み込む
    driver.get(pageurl)
    sleep(10 * random())
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')

    # outputHTML(html, tag='beforeInputs')

    # email, passwordの入力欄があれば、クリアしてから入力する
    if soup.find(name='input', id='ap_email'):
        driver.find_element_by_id('ap_email').clear()
        sleep(10 * random())
        driver.find_element_by_id('ap_email').send_keys(username)
        sleep(10 * random())
    if soup.find(name='input', id='ap_password'):
        driver.find_element_by_id('ap_password').clear()
        sleep(10 * random())
        driver.find_element_by_id('ap_password').send_keys(password)
        sleep(10 * random())
    # captchaがあればそれも入力
    if soup.find(name='div', id='image-captcha-section'):
        captchaCode = getCaptchaCode(html)
        driver.find_element_by_id('image-captcha-section').send_keys(captchaCode)
        sleep(10 * random())

    # ボタンを押して送信したい
    if soup.find(name='input', id='signInSubmit'):
        print('Trying button submit ...\n')
        loginButton = driver.find_element_by_id('signInSubmit')
        driver.execute_script("arguments[0].click();", loginButton)
        sleep(30 * random())
    elif soup.find(name='input', id='continue'):
        print('Trying OTP ...\n')
        continueButton = driver.find_element_by_id('continue')
        driver.execute_script("arguments[0].click();", continueButton)
        sleep(30 * random())
    
    # outputHTML(html, tag='afterSend')

    # ----------- 状況によって、CaptchaかOTPか変化する（どちらが先にくるかわからない）
    # for debug
    print('button has push.\n')
    # outputHTML(driver.page_source, tag="afterPush")

    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')

    # Captchaを提示された場合
    if soup.find(name='div', id='image-captcha-section'):
        login(driver.current_url, driver)
    # OTPを要求された場合
    elif soup.find(name='input', maxlength='6'):  
        # ワンタイムパスワードの入力画面へ進む
        otpCode = getOTP()
        driver.find_element_by_xpath("//input[@type='text'][@name='code'][@maxlength='6']").send_keys(otpCode)
        # continue ボタンを押す
        continueButton = driver.find_element_by_id('continue')
        driver.execute_script("arguments[0].click();", continueButton)
        sleep(30 * random())
    elif soup.find(name='input', id='continue'):
        # continue ボタンを押す
        login(driver.current_url, driver)
    
    if soup.find(name='a', href='https://www.amazon.com'):
        driver.find_element_by_xpath("//a[@href='{}']".format('https://www.amazon.com')).click
        sleep(10 * random())

    return driver

def countPages(driver):

    # クエリからページ数とコンテンツ数を指定して対象とするページの一覧を集める
    rootURL = 'https://worker.mturk.com/?page_number=1&page_size=100'
    driver.get(rootURL)
    sleep(20 * random())
    html = driver.page_source
    # outputHTML(html, tag='inCountingPages')
    print(driver.current_url)
    sleep(10 * random())

    # data-react-class="require('reactComponents/navigation/Pagination')['default']"
    soup = BeautifulSoup(html, 'lxml')
    target = "require('reactComponents/navigation/Pagination')['default']"

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
    target_dir.mkdir(parents=True, exist_ok=True)
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

    with open(filepath, mode='w', encoding='utf-8') as f:
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
    # outputHTML(driver.page_source, tag="afterLogin")
    page_list = countPages(driver)
    json_dict = getHITContent(page_list)
    outputJSON(json_dict)

    timestamp = datetime.now(tz_jst).isoformat(timespec='seconds')
    print('{} ... STATUS: complete.'.format(timestamp))

except Exception as e:
    print(datetime.now(tz_jst).isoformat(timespec='seconds'), file=sys.stderr)
    print('USER EXCEPTION ! : ' + str(e), file=sys.stderr)
    # outputHTML(driver.page_source, tag="anyExceptions")


try:
    driver.quit()
    print('Driver has stopped.\n')
except NameError as ne:
    print(str(ne), file=sys.stderr)
