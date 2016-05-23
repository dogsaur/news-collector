# encoding: utf-8
import os
import json
import pickle
import datetime
import re
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

import check_result
import utils
import db

COOKIE_FILE = 'cookies.pkl'
DOWN_CONFIG = 'download_config.json'


def load_cookie(driver, cookie_file):
    driver.get("http://www.5730.net/")
    cookie_file = "cookies.pkl"
    if os.path.isfile(cookie_file):
        cookies = pickle.load(open(cookie_file, 'rb'))
        for cookie in cookies:
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print(e)
    else:
        input('<-cookie不存在请手动登陆后, 输入 enter')
        pickle.dump(driver.get_cookies(), open(cookie_file, "wb"))
    driver.refresh()
    driver.set_page_load_timeout(20)
    if not down_config['auto_select_entrance']:
        input("<-请选择通道后, 输入 enter")
    else:
        driver.find_element_by_partial_link_text('知网数据库').click()
        goto_window_contains_text(driver, "知网数据库_5730")
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")
        driver.find_element_by_xpath(
            '//a[@href="http://www.5730.net/showinfo-10-145-0.html"]').click()
        # input('gg')

        for handle in driver.window_handles:
            driver.switch_to_window(handle)
            # sleep(1)
            try:
                alert = driver.switch_to_alert()
                alert.accept()
            except Exception as e:
                print('no alert')
        driver.set_page_load_timeout(20)
        goto_window_contains_text(driver, "选择平台入口")
        driver.set_page_load_timeout(20)
        # driver.find_element_by_class_name('body').send_keys(Keys.ENTER)
        driver.find_element_by_partial_link_text("知识发现网络平台").click()
        # input("go")


def load_download_config(config):
    if os.path.isfile(config):
        return json.load(open(config, 'r', encoding='utf-8'))
    else:
        return {
            'source': '上海证券报',
            'date_from': '2015-5-1',
            'date_to': '2015-5-31',
            'version': 1,
            'down_time_sep': 10,
            'load_time_out': 20,
            'auto_mode': True,
            'auto_select_entrance': True}

down_config = load_download_config(DOWN_CONFIG)


def goto_window_contains_text(driver, text):
    # win_handle_before = driver.get_window_handle()
    # print('start goto window'#)
    for handle in driver.window_handles:
        driver.switch_to_window(handle)
        if text in driver.title:
            # print('move to ', driver.title)
            return
    # print('can not find target window', text)
    # driver.switch_to_window(win_handle_before)


def goto_frame(driver, frameID):
    iframe = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.ID, frameID)))
    driver.switch_to.frame(iframe)


def init_retrieve_page(driver):
    driver.get("http://epub.cnki.net/kns/brief/result.aspx?dbPrefix=CCND")
    print("->选择类型...")
    type_sel = Select(driver.find_element_by_name("txt_1_sel"))
    type_sel.select_by_visible_text("报纸名称")

    print("->输入文章来源...")
    source_input = driver.find_element_by_id("txt_1_value1")
    source_input.send_keys(down_config['source'])

    print("->选择年份...")
    date_from = driver.find_element_by_id("publishdate_from")
    date_from.send_keys(down_config['date_from'])

    date_to = driver.find_element_by_id("publishdate_to")
    date_to.send_keys(down_config['date_from'])

    print("->开始检索...")
    search_bt = driver.find_element_by_id("btnSearch")
    if search_bt is not None:
        search_bt.click()

    # 寻找验证码 否则抛出异常

    print("->定位到 iframe...")
    goto_frame(driver, 'iframeResult')

    print("->选择50项每页...")
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.LINK_TEXT, '50'))).click()

    print("->初始化成功...")

    count_str = driver.find_element_by_class_name('pagerTitleCell').text

    count = int(re.search(r'\d+', count_str).group())

    db.update_date_info(down_config['source'],
                        down_config['date_from'], count)
    # input('gg')


def iterate_page(driver, is_get_token=False):
    while True:
        links = driver.find_elements_by_class_name('fz14')
        for i in range(len(links)):
            goto_window_contains_text(driver, "中国重要报纸")
            goto_frame(driver, 'iframeResult')
            links = driver.find_elements_by_class_name('fz14')
            link = links[i]
            doc_name = link.get_attribute("text")
            # if doc_name not in doc_dict:
            if db.session.query(
                db.Record).filter_by(
                title=doc_name).first(
            ) is None:
                print('->抓取第', '项...', doc_name)
                tr = link.find_element_by_xpath('../..')
                date = tr.find_element_by_xpath(
                    "//td[contains(text(), '2009')]").text
                pdf_url = link.get_attribute('href')

                down_config['date_from'] = date
                record_dict = {"name": str(doc_name),
                               "date": date,
                               "pdf_url": pdf_url,
                               "source": '中国证券报',
                               "status": 'downloading'}
                db.add_record(record_dict)
            else:
                print('->already done, skiped', doc_name)

        goto_window_contains_text(driver, "中国重要报纸")
        goto_frame(driver, 'iframeResult')

        print("->跳转下一页...")
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.ID, 'Page_next'))).click()
        except Exception:
            print('-> can not got next page')
            print('-> ', down_config['date_from'], 'finished, next day...')
            d = datetime.datetime.strptime(
                down_config['date_from'], "%Y-%m-%d")
            d += datetime.timedelta(days=1)
            down_config['date_from'] = d.strftime("%Y-%m-%d")
            return


def run():
    load_cookie(driver, COOKIE_FILE)

    while True:
        init_retrieve_page(driver)
        input('gg')
        iterate_page(driver)


if __name__ == '__main__':
    try_cnt = 1
    while down_config['date_from'] != down_config['date_to']:
        print('开始进行第', try_cnt, '次尝试...')
        driver = webdriver.Chrome()
        driver.set_page_load_timeout(20)
        try_cnt += 1
        try:
            run()
        except NoSuchElementException as e:
            print(e)
        except TimeoutException as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            try:
                driver.quit()
            except Exception as e:
                print(e)
            finally:
                print('->保存配置文件...')
                json.dump(down_config,
                          open(DOWN_CONFIG, 'w', encoding='utf-8'),
                          ensure_ascii=False, indent=4)


