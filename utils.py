import os
import json

DICT_FILE = 'doc_info_dict.json'
DOWN_CONFIG = 'download_config.json'


def load_download_config(config=DOWN_CONFIG):
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


def load_doc_dict(doc_dict_file=DICT_FILE):
    if os.path.isfile(doc_dict_file):
        return json.load(open(doc_dict_file, 'r', encoding='utf-8'))
    else:
        return dict()


def dump_doc_dict(doc_dict, doc_dict_file=DICT_FILE):
    while True:
        try:
            json.dump(doc_dict, open(
                doc_dict_file,
                'w',
                encoding='utf-8'),
                ensure_ascii=False, indent=4)
            break
        except Exception as e:
            print(e)
            if input('是否重新保存? y/n') == 'n':
                break
