import utils
import os


def mapping(record):
    translation_table = dict.fromkeys(map(ord, '：\'\":”“()＋+/.%、-？*'), '_')
    tag = record.replace(' ', '').translate(translation_table)
    tag = tag.replace('_', '')
    tag = tag[:10]
    return tag

def r_mapping(filename):
    r_index = filename.rfind('_')
    tag = filename[0:r_index]
    tag = tag.replace('_', '')
    return tag[:10]

config = utils.load_download_config()
records = utils.load_doc_dict()
DOWNLOAD_PATH = config['download_path']

print('->加载下载记录...')
print('共计 %d 记录' % len(records))

print('->校对下载目录: ', DOWNLOAD_PATH)
print('->共计 %d 文件' % len(os.listdir(DOWNLOAD_PATH)))
result_files = {}
for file in os.listdir(DOWNLOAD_PATH):
    if not os.path.isfile(os.path.join(DOWNLOAD_PATH, file)):
        continue
    if '.pdf' not in file:
        continue
    tag = r_mapping(file)
    result_files[tag] = {'filename': file}

print('->其中 %d pdf文件' % len(result_files))

cnt = 0
for record in records:
    tag = mapping(record)
    # print('tag: ', tag)
    if tag in result_files:
        # print('file: ', file)
        flag = False
        records[record]['filename'] = result_files[tag]['filename']
        records[record]['status'] = 'finished'
        result_files.pop(tag)
        cnt += 1

print('->注意! %d 文件未被对应, 请在 unused_files 中检查' % len(result_files))

print('->共找到 %d 对匹配' % cnt)
print('-> %d 记录未找到文件' % (len(records) - cnt))
print('->更新下载状态...')
# utils.dump_doc_dict(result_files, doc_dict_file='unused_files.json')
utils.dump_doc_dict(records)
print('->更新成功')
