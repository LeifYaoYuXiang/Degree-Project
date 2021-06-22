# -*- coding:utf8 -*-
import multiprocessing
# 监听本机的3389端口
bind = '0.0.0.0:3389'        
workers = multiprocessing.cpu_count() * 2 + 1
threads = multiprocessing.cpu_count() * 2
daemon = True
worker_class = "gevent"
