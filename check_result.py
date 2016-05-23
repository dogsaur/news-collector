import os, re
import utils
import db
from sqlalchemy.sql import func


def mapping(record):
    translation_table = dict.fromkeys(
        map(ord, 'β！：∶\n‰\'\":”“()（）＋+/.%、~—·≠《!=…,》-？*'), '_')
    tag = record.replace(' ', '').translate(translation_table)
    tag = tag.replace('_', '')
    tag = tag[:15]
    return tag


def r_mapping(filename):
    r_index = filename.rfind('_')
    tag = filename[0:r_index]
    tag = tag.replace('_', '')
    return tag[:15]


config = utils.load_download_config()
DOWNLOAD_PATH = config['download_path']
def check():
    records = db.session.query(db.Record).all()

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
    for i in range(1, 10):
        for record in records:
            tag = mapping(record.title)
            if tag in result_files:
                # print('find')
                # print('find %s', tag)
                record.filename = result_files[tag]['filename']
                record.status = 1
                result_files.pop(tag)
                cnt += 1

        tmp = result_files
        result_files = {}
        for tag in tmp:
            if len(tag) > 5:
                result_files[tag[:-1]] = tmp[tag]
            # print(tag)
        # print('-----------')

    print('->注意! %d 文件未被对应, 请在 unused_files 中检查' % len(result_files))

    print('->共找到 %d 对匹配' % cnt)
    print('-> %d 记录未找到文件' % (len(records) - cnt))
    print('->更新下载状态...')
    db.session.commit()
    utils.dump_doc_dict(result_files, doc_dict_file='unused_files.json')
    # utils.dump_doc_dict(records)

    print('->更新成功')


def remove_dumplicate_files():
    files_to_rm = []
    for file in os.listdir(DOWNLOAD_PATH):
        if os.path.splitext(file)[-1] == '.pdf' and re.search(r'\(\d+\)', file) is not None:
            # print(file)
            # print('[%s]' % os.path.splitext(file)[-1])
            files_to_rm.append(file)
    if input('assure to rm? y/n') == 'y':
        for file in files_to_rm:
            os.remove(os.path.join(DOWNLOAD_PATH, file))
        print('removed')


def count_by_month():
    month_count = [0] * 12
    records = db.session.query(db.Record).all()
    for record in records:
        month_count[record.publish_date.month - 1] += 1
    for i in range(12):
        print('%d 月共有 %d 条记录' % (i + 1, month_count[i]))


def count_by_day():
    records = db.session.query(db.Record).all()
    day_count = {}
    for record in records:
        date_str = record.publish_date.strftime("%Y-%m-%d")
        source = record.source
        key = source + ':' + date_str
        if key in day_count:
            day_count[key] += 1
        else:
            day_count[key] = 0

    for key in day_count:
        qu = db.session.query(
            db.DateInfo).filter_by(key=key)
        if qu.first() is not None:
            qu.update(
                {'actual_record_count': day_count[key]})
            print('update %s actual count to %d' % (key, day_count[key]))
        else:
            continue
    db.session.commit()


if __name__ == '__main__':
    # count_by_month()
    # count_by_day()
    # for di in db.session.query(db.DateInfo).all():
    #     print(di)
    check()
    remove_dumplicate_files()
    print(mapping('峨眉山A(000888)索道提价预期强烈'))
    print(r_mapping('全国政协委员_中煤能源集团原总经_省略_亮_今年煤炭供需总体平衡局部紧张_周明 (2).pdf.pdf'))
