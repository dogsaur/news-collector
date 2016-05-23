# encoding: utf-8
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.exc import IntegrityError

import utils

engine = create_engine('sqlite:///app.db')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class Record(Base):
    __tablename__ = 'record'
    title = Column(String, primary_key=True)
    filename = Column(String)
    publish_date = Column(DateTime)
    source = Column(String)
    status = Column(Integer)
    page_url = Column(String)
    download_url = Column(String)

    def __repr__(self):
        if self.status == 1:
            status_str = 'finished'
        else:
            status_str = 'downloading'
        return '<Record(%s, %s)>' % (self.title, status_str)


class DateInfo(Base):
    __tablename__ = 'dl_date_info'
    key = Column(String, primary_key=True)
    source = Column(String)
    date = Column(DateTime)
    record_count = Column(Integer)
    actual_record_count = Column(Integer)

    def __repr__(self):
        return '<DateInfo<%s, %d/%d>' % (self.key,
                                         self.actual_record_count,
                                         self.record_count)

Base.metadata.create_all(engine)


def update_date_info(source, date_str, record_count, actual_record_count=0):
    date = datetime.strptime(date_str, '%Y-%m-%d')
    key = source + ':' + date_str
    if session.query(DateInfo).filter_by(key=key).first() is not None:
        return

    date_info = DateInfo(key=key, date=date,
                         record_count=record_count,
                         actual_record_count=actual_record_count)
    print('adding %s' % date_info)
    session.add(date_info)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def add_record(record_dict):
    title = record_dict['name']
    if session.query(Record).filter_by(title=title).first() is not None:
        return
    filename=''
    if 'filename' in record_dict:
        filename = record_dict['filename']
    else:
        pass
    page_url = record_dict['pdf_url']
    # source = record_dict['source']
    source = '中国证券报'
    publish_date = datetime.strptime(
        record_dict['date'], '%Y-%m-%d')

    if record_dict['status'] == 'finished':
        status = 1
    else:
        status = 0

    record = Record(title=title,
                    filename=filename,
                    page_url=page_url,
                    source=source,
                    publish_date=publish_date,
                    status=status)
    # print(record)
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()


def add_records():
    dict_records = utils.load_doc_dict()
    for item in dict_records:
        add_record(dict_records[item])

if __name__ == '__main__':
    # for di in session.query(DateInfo).all():
    #     session.query(DateInfo).filter_by(key=di.key).update(
    #         {'actual_record_count': 0})
    #     print(di.actual_record_count)
    add_records()
    # dict_records = utils.load_doc_dict()
    # print(len(dict_records))
    # add_records(dict_records)
    # session = Session()
    # records = session.query(Record).all()
    # print(len(records))
    # for record in records:
    #     print(record)
    pass