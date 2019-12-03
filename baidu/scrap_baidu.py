# -*- coding: utf-8 -*-

import re
import os
import sys
import json
import subprocess
from time import sleep
from pathlib import Path
from random import random
from datetime import datetime, date, timezone, timedelta

# need to pip install
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import exceptions
from pyvirtualdisplay import Display
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

''' 使わなくなった自作関数
    def getPageList(driver):

    #指定したdriverに対して最大で60秒間待つように設定する
    wait = WebDriverWait(driver, 60)
    #指定された要素が表示状態になるまで待機する
    # # <li ng-if="pagination.currentPage < pagination.totalPage - 3 && pagination.totalPage > 5">
    # # <a ng-click="setPage(pagination.totalPage)" ng-bind="pagination.totalPage"></a> </li>
    pagination_xpath = "//a[@ng-bind='pagination.totalPage']"
    wait.until(EC.visibility_of_element_located((By.XPATH, pagination_xpath)))

    soup = BeautifulSoup(driver.page_source, 'lxml')
    # ng-bind="pagination.totalPage" class="ng-binding"
    totalPage = soup.find(name='a', attrs={"ng-bind": "pagination.totalPage"}, class_='ng-binding').text

    page_list = []
    page_list.append(driver.page_source)  # first page only 


    for _ in range(int(totalPage) - 1):
        # <li ng-class="{false:'unCommit'}[isLastCommit]"><a ng-click="nextPage()">下一页</a></li>
        # nextPageXpath = "//li[contains(@ng-class, 'isLastCommit')]"
        nextPageXpath = "//a[contains(text(), '下一页')]"
        nextButton = driver.find_element_by_xpath(nextPageXpath)
        # クリックしたい要素までスクロール
        driver.execute_script("arguments[0].scrollIntoView(true);", nextButton)
        # クリック実行
        wait.until(EC.element_to_be_clickable((By.XPATH, nextPageXpath)))
        nextButton.click()
        # driver.execute_script("arguments[0].click();", nextButton)


        # <li ng-repeat="page in pagination.pages" ng-class="{true:'active'}[page===pagination.currentPage]" class="ng-scope">
        #     <a ng-bind="2" ng-click="setPage(page)" class="ng-binding">2</a>
        # </li>
        sleep(5 * random())
        page_list.append(driver.page_source)

    return page_list

    def convertJSON(task_list):

        pattern_comment = re.compile('<!--[\s\S]*?-->')
        pattern_strip = re.compile('[\t\n]+')
        
        html = '<!DOCTYPE html><html><head></head><body><ul>{}</ul></body></html>'.format(''.join(task_list))
        html = pattern_comment.sub('', html)
        html = pattern_strip.sub('', html)
        html = BeautifulSoup(html, 'lxml').prettify()

        outputHTML(html, tag='with_tasklist')

        return 'OK'
'''


def initializeDriver():

    tz_jst = timezone(timedelta(hours=9))

    print('START: {}'.format(datetime.now(tz_jst).isoformat(timespec='seconds')))
    # set virtual display via Xvfb
    print('Setting virtual window ...')
    display = Display(visible=0, size=(1920, 1080))
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
    # driver = webdriver.Chrome(executable_path='/home/kiai/.local/bin/chromedriver', options=options)
    driver.set_window_size(1920, 1080)  # for Virtualdisplay
    print('webDriver is ready!')

    return driver

def outputHTML(html, tag=""):
    
    tz_jst = timezone(timedelta(hours=9))

    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_BAIDU', 'task')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d')
    target_dir.mkdir(exist_ok=True)
    if len(tag) != 0:
        filepath = target_dir / '{}_{}.html'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'), tag)
    else:
        filepath = target_dir / '{}.html'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))

    with open(filepath, mode='w', encoding='utf-8') as f:
        f.write(html)

def outputJSON(json_list, tag=""):

    tz_jst = timezone(timedelta(hours=9))

    current_dir = Path.cwd()
    volume = os.environ.get('DATA_VOLUME_BAIDU', 'task')
    target_dir = current_dir / volume / datetime.now(tz_jst).strftime('%Y%m%d')
    target_dir.mkdir(exist_ok=True)

    if len(tag):
        filepath = target_dir / '{0}_{1}.json'.format(tag, datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))
    else:
        filepath = target_dir / '{}.json'.format(datetime.now(tz_jst).strftime('%Y%m%d_%H%M%S'))
    
    if len(json_list) == 0:
        status = 'failure'
    else:
        status = 'OK'

    temp_dict = {
        'service': 'test.baidu.com/{}'.format(tag),
        'timestamp': datetime.now(tz_jst).isoformat(timespec='seconds'),
        'status': status,
        'content': json_list
    }  

    with open(filepath, mode='w',encoding='utf-8') as f:
        f.write(json.dumps(temp_dict, indent=4, ensure_ascii=False))


def getTaskContent(driver, url):

    driver.get(url)

    #指定したdriverに対して最大で60秒間待つように設定する
    wait = WebDriverWait(driver, 60)
    #指定された要素が表示状態になるまで待機する
    # # <li ng-if="pagination.currentPage < pagination.totalPage - 3 && pagination.totalPage > 5">
    # # <a ng-click="setPage(pagination.totalPage)" ng-bind="pagination.totalPage"></a> </li>
    pagination_xpath = "//a[@ng-bind='pagination.totalPage']"
    wait.until(EC.visibility_of_element_located((By.XPATH, pagination_xpath)))

    allCookies = driver.get_cookies()

    cookie_dict = {cookie['name']:cookie['value'] for cookie in allCookies}
    
    headers =  {
        'referer': 'https://test.baidu.com/mark/task/index',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'X-Requested-With': 'XMLHttpRequest',
        'X-YII-CSRF-TOKEN': os.environ.get('BAIDU_CSRF_TOKEN', 'default')
    }
    
    resp = requests.get('https://test.baidu.com/mark/task/getList', cookies=cookie_dict, headers=headers)
    
    sleep(20 * random()) 

    outputJSON(json.loads(resp.text), tag="test")

    return driver


def getSurveyContent(driver, url):
    
    driver.get(url)

    # #指定したdriverに対して最大で60秒間待つように設定する
    # wait = WebDriverWait(driver, 60)
    # #指定された要素が表示状態になるまで待機する
    # # <li ng-class="{false:'unCommit'}[isLastCommit]"><a ng-click="nextPage()">下一页</a></li>
    # pagination_xpath = "//li[@ng-class='{false:'unCommit'}[isLastCommit]']"
    # wait.until(EC.visibility_of_element_located((By.XPATH, pagination_xpath)))

    # 要素が取れないので保留
    sleep(60)

    allCookies = driver.get_cookies()

    cookie_dict = {cookie['name']:cookie['value'] for cookie in allCookies}
    
    headers =  {
        'referer': 'https://test.baidu.com/crowdtest/activityUnit/paperSurvey/type/2',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'X-Requested-With': 'XMLHttpRequest',
        'X-YII-CSRF-TOKEN': os.environ.get('BAIDU_CSRF_TOKEN', 'default')
    }
    
    resp = requests.get('https://test.baidu.com/crowdtest/n/project/list/type/2', cookies=cookie_dict, headers=headers)

    sleep(20 * random()) 

    json_dict = json.loads(resp.text)
    survey_list = [v for k, v in json_dict.items()]

    outputJSON(survey_list, tag="survey")

    return driver

# ここから本番 -------------------------------------------

# log stdout
tz_jst = timezone(timedelta(hours=9))

try:
    driver = initializeDriver()
    rootURL = 'https://test.baidu.com/mark/task/index'
    getTaskContent(driver, rootURL)

    rootURL = 'https://test.baidu.com/crowdtest/activityUnit/paperSurvey/type/2'
    getSurveyContent(driver, rootURL)

    timestamp = datetime.now(tz_jst).isoformat(timespec='seconds')
    message = 'DATA_VOLUME_BAIDU: {}\n'.format(os.environ.get('DATA_VOLUME_BAIDU', 'ENV is not configured!'))
    print(timestamp + '...' + message)

except Exception as e:
    print(datetime.now(tz_jst).isoformat(timespec='seconds'))
    print('USER EXCEPTION ! : ' + str(e))

try:
    driver.quit()
    print('Driver has stopped.\n')
except NameError as ne:
    print(str(ne), file=sys.stderr)
