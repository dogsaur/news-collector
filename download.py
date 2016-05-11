import os
import json
import pickle
from time import sleep
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


DICT_FILE = 'doc_info_dict.json'
COOKIE_FILE = 'cookies.pkl'
DOWN_CONFIG = 'download_config.json'


def load_doc_dict(doc_dict_file):
    if os.path.isfile(doc_dict_file):
        return json.load(open(doc_dict_file, 'r'))
    else:
        return dict()


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
    input("<-请选择通道后, 输入 enter")


def load_download_config(config):
    if os.path.isfile(config):
        return json.load(open(config, 'r'))
    else:
        return {
            'source': '上海证券报',
            'date_from': '2015-5-1',
            'date_to': '2015-5-31',
            'version': 1,
            'down_time_sep': 10,
            'load_time_out': 20,
            'auto_mode': True}

doc_dict = load_doc_dict(DICT_FILE)
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
    date_to.send_keys(down_config['date_to'])

    print("->开始检索...")
    search_bt = driver.find_element_by_id("btnSearch")
    if search_bt is not None:
        search_bt.click()

    print("->定位到 iframe...")
    goto_frame(driver, 'iframeResult')

    print("->选择50项每页...")
    WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.LINK_TEXT, '50'))).click()

    print("->按照日期排序...")
    img_src = ''
    while 'icon-u' not in img_src:
        order_by = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, '报纸日期')))
        order_by.click()
        order_by = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable(
                (By.LINK_TEXT, '报纸日期')))
        img = order_by.find_element_by_tag_name('img')
        img_src = img.get_attribute('src')

    print("->初始化成功...")


def iterate_page(driver):
    while True:
        links = driver.find_elements_by_class_name('fz14')
        for i in range(len(links)):
            goto_window_contains_text(driver, "中国重要报纸")
            goto_frame(driver, 'iframeResult')
            links = driver.find_elements_by_class_name('fz14')
            link = links[i]
            doc_name = link.get_attribute("text")
            if doc_name not in doc_dict:
                print('->抓取第', len(doc_dict), '项...', doc_name)
                #url = link.get_attribute("href")
                tr = link.find_element_by_xpath('../..')
                date = tr.find_element_by_xpath(
                    "//td[contains(text(), '2015')]").text
                pdf_url = link.get_attribute('href')
                # print('->open in new tab...')
                try:
                    driver.set_page_load_timeout(20)
                    link.click()
                except Exception as e:
                    print('time out')
                    driver.send_keys('Escape')
                # print('->open success...')
                #driver.manage().timeouts().pageLoadTimeout(5, TimeUnit.SECONDS);
                goto_window_contains_text(driver, doc_name)
                print(driver.title)
                download_link = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable(
                        (By.PARTIAL_LINK_TEXT, 'PDF下载')))
                #download = driver.find_element_by_partial_link_text("PDF下载")
                # download.click()


                print('->downloading... [', doc_name, ']')
                #download(driver, pdf_url)
                download_link.click()
                print('->success!')
                if down_config['auto_mode']:
                    sleep(down_config['down_time_sep'])
                else:
                    input("->press enter to continue")
                # input("continue")
                try:
                    driver.close()
                except Exception as e:
                    print(e)

                down_config['date_from'] = date
                doc_dict[doc_name] = {"name": str(doc_name),
                                      "date": date,
                                      "pdf_url": pdf_url,
                                      "source": '上海证券报',
                                      "status": 'downloading'}

            else:
                print('->already done, skiped', doc_name)

        goto_window_contains_text(driver, "中国重要报纸")
        goto_frame(driver, 'iframeResult')

        print("->跳转下一页...")
        WebDriverWait(driver, 50).until(
            EC.element_to_be_clickable(
                (By.ID, 'Page_next'))).click()


def download(driver, url):
    print(url)
    driver.get(url)


def run():
    init_retrieve_page(driver)
    iterate_page(driver)


def check_download_result(path):
    local_files = set()
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            print(file)
        #TODO: check download result



driver = webdriver.Chrome()
if __name__ == '__main__':
    load_cookie(driver, COOKIE_FILE)
    try_cnt = 1
    while down_config['date_from'] != down_config['date_to']:
        print('开始进行第', try_cnt, '次尝试...')
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
            down_config['version'] += 1
            print('->保存下载状态...')
            json.dump(doc_dict, open(DICT_FILE +
                                     '.' + str(down_config['version']), 'w'),
                      ensure_ascii=False, indent=4)
            json.dump(doc_dict, open(DICT_FILE, "w"),
                      ensure_ascii=False, indent=4)
            print('->保存配置文件...')
            json.dump(down_config, open(DOWN_CONFIG, 'w'),
                      ensure_ascii=False, indent=4)
