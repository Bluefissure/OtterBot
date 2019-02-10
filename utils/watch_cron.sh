mkdir log
killall watch
nohup watch -n 60 python crawl_wb.py >> log/crawl_wb.log &
