import re
import db

records = db.session.query(db.Record).all()

for record in records:
	if record.status == 0:
		print(record.title)
		if input('y/n')=='y':
			record.status = 1
			db.session.commit()
