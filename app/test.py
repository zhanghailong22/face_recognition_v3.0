#!/usr/bin/python
# -*- coding: utf-8 -*-
# test face_recognition_app.py

import requests

# 录入
url = "http://127.0.0.1:9999/upload"

filepath = '/home/face_recognition_v3.0/examples/biden.jpg'
split_path = filepath.split('/')
filename = split_path[-1]

file = open(filepath, 'rb')
files = {'file': (filename, file, 'image/jpg')}
print(files)
r = requests.post(url, files=files)
result = r.text
print(result)

# 查询
url = "http://127.0.0.1:9999/search_images"

filepath = '/home/face_recognition_v3.0/examples/two_people.jpg'
split_path = filepath.split('/')
filename = split_path[-1]
print(filename)

file = open(filepath, 'rb')
files = {'file': (filename, file, 'image/jpg')}

r = requests.post(url, files=files)
result = r.text
print(result)

# # 视频监控
# url = "http://127.0.0.1:9999/search_video"
#
# r = requests.post(url)
# result = r.text
# print(result)

# 刷新redis
url = "http://127.0.0.1:9999/refresh_redis"

r = requests.post(url)
result = r.text
print(result)
