mkdir log
ps -ef | grep "python crawl" | grep -v grep | cut -c 9-15 | xargs kill -s 9
nohup python crawl_wb.py &
nohup python crawl_live.py &
