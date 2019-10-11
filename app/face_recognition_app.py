#!/usr/bin/python
# -*- coding: utf-8 -*-
# This is an app application for face recognition microservices.
# Its functions are: face upload, face recognition, Video face recognition, etc.
# The restfull api is http://127.0.0.1:9999. Database is redis, used to store
# the feature vector of the face.
# Store face images in data volume mysql
# Author e-mail:zhanghailong22@huawei.com
#
import os
import pymysql
import video_camera
from flask import Flask, Response, request, jsonify
import redis
import face_recognition
import numpy as np
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 允许上传的文件类型：png、jpg、jpeg。
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# 连接redis
pool = redis.ConnectionPool(host='127.0.0.1', port=6379)
# pool = redis.ConnectionPool(host='redis', port=6379)

# 图像录入
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'code': 500, 'msg': '没有文件'})
    files = request.files.getlist("file")
    conn = pymysql.Connect(host='127.0.0.1', user='root', password='root', port=3306, database='face_images')
    cursor = conn.cursor()
    num = 0
    for file in files:
        if file.filename == '':
            break
        if file and allowed_file(file.filename):
            # 保存在mysql数据库中
            img = file.read()
            name = file.filename[0:-4]
            sql = 'insert ignore into image_data (name,image) values(%s, %s);'
            data = [(name, pymysql.Binary(img))]
            cursor.executemany(sql, data)
            conn.commit()
        else:
            return jsonify({'error': '图片格式错误'})
        num = num+1
        # 将人脸向量保存在redis数据库
        image = face_recognition.load_image_file(file)
        face_locations = face_recognition.face_locations(image)
        if len(face_locations) != 1:
            return jsonify({'code': 500, 'error': '人脸数量有误'})
        face_encodings = face_recognition.face_encodings(image, face_locations)
        # 连数据库
        r = redis.Redis(connection_pool=pool)
        # 录入人名-对应特征向量
        r.set(name, face_encodings[0].tobytes())
    cursor.close()
    conn.close()
    return jsonify({'number': num, 'result': '录入成功'})

# 人脸搜索
@app.route('/search_images', methods=['POST'])
def searchImages():
    if 'file' not in request.files:
        return jsonify({'code': 500, 'result': '没有文件'})
    file = request.files['file']
    if allowed_file(file.filename) == 0:
        # The image file seems valid! Detect faces and return the result.
        return jsonify({'error': '图片格式错误'})

    image = face_recognition.load_image_file(file)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)
    # 连数据库
    r = redis.Redis(connection_pool=pool)
    # 取出所有的人名和它对应的特征向量
    names = r.keys()
    faces = r.mget(names)
    # 组成矩阵，计算相似度（欧式距离）
    find_names = []
    number = len(face_encodings)
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces([np.frombuffer(x) for x in faces], face_encoding)
        for name, match in zip(names, matches):
            if match:
                find_names.append(name)
                break

    return jsonify({'图片中人脸的个数': number, '查询到的人脸个数': len(find_names), \
                    "find_names": [str(name, 'utf-8') for name in find_names]})
#   return jsonify({'code': 0, 'names': [str(name, 'utf-8') for name, match in zip(names, matches) if match]})

# 视频监控
@app.route('/search_video', methods=['POST'])
def searchVideo():
    # 连数据库
    r = redis.Redis(connection_pool=pool)
    # 取出所有的人名和它对应的特征向量
    names = r.keys()
    faces = r.mget(names)
    # 组成矩阵，计算相似度（欧式距离）
    face_names = video_camera.video_camera(names, faces)

    return jsonify({'names': face_names})

# 刷新redis，将mysql数据库中的人脸图片生成特征向量并导入redis数据库
@app.route('/refresh_redis', methods=['POST'])
def updateRedis():
    # 1.连接mysql数据库
    conn = pymysql.connect(host='127.0.0.1', user='root', password='root', port=3306, database='face_images')
    # 2.创建游标
    cursor = conn.cursor()
    sql = "select * from image_data"
    cursor.execute(sql)  # 执行sql
    # 查询所有数据，返回结果默认以元组形式，所以可以进行迭代处理
    r = redis.Redis(connection_pool=pool)
    for i in cursor.fetchall():
        name = i[0]
        fout = open('image.jpg', 'wb')
        fout.write(i[1])
        file = open('image.jpg', 'rb')
        image = face_recognition.load_image_file(file)
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        # 录入人名-对应特征向量
        r.set(name, face_encodings[0].tobytes())
    cursor.close()
    conn.close()
    names = r.keys()

    return jsonify({'redis中人脸数目': len(names), 'result': '刷新成功'})

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=9999)
