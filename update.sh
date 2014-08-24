cd `dirname $0`
date >> log/update.log
./manage.py update
