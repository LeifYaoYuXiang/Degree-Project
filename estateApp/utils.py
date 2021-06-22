import requests
from flask import session
from estateApp.models import NewHouse, SecondHouse, Publish
from pypinyin import pinyin, lazy_pinyin, Style

import numpy as np
import pickle
import json

model = ''

# 高德地图申请头
from estateApp.models import User

current_key = '17bfdf31fa5f138372b6733877f875e1'
weekday = {
    '1': 'Monday',
    '2': 'Tuesday',
    '3': 'Wednesday',
    '4': 'Thursday',
    '5': 'Friday',
    '6': 'Saturday',
    '7': 'Sunday'
}

# 根据价格分层
def category_price(price):
    if price < 5000:
        return "col-xl-3 col-lg-3 col-md-6 grid-item cat1"
    elif price >= 5000 and price < 7500:
        return "col-xl-3 col-lg-3 col-md-6 grid-item cat2"
    elif price >= 7500 and price < 10000:
        return "col-xl-3 col-lg-3 col-md-6 grid-item cat3"
    elif price >= 10000 and price < 12500:
        return "col-xl-3 col-lg-3 col-md-6 grid-item cat4"
    elif price >= 12500 and price < 15000:
        return "col-xl-3 col-lg-3 col-md-6 grid-item cat5"
    else:
        return "col-xl-3 col-lg-3 col-md-6 grid-item cat6"

# 将地址转化为经纬度
def ExcuteSingleQuery(locationList):
    # 1-将locationList中的地址连接成高德地图API能够识别的样子
    locationString = ""     # 当前locationList组成的string
    for location in locationList:
        locationString += location + '|'
    # 2-地理编码查询需要的Url
    output = 'json'    # 查询返回的形式
    batch = 'true'     # 是否支持多个查询
    base = 'https://restapi.amap.com/v3/geocode/geo?' # 地理编码查询Url的头
    currentUrl = base + "output=" + output + "&batch=" + batch + "&address=" + locationString + "&key=" + current_key
    # 3-提交请求
    response = requests.get(currentUrl)    # 提交请求
    if response.status_code == 200:
        answer = response.json()   # 接收返回
        # 4-解析Json的内容
        resultList = []    # 用来存放地理编码结果的空序列
        if answer['status'] == '1' and answer['info'] == 'OK':
            # 4.1-请求和返回都成功，则进行解析
            tmpList = answer['geocodes']    # 获取所有结果坐标点
            for i in range(0,len(tmpList)):
                try:
                    # 解析','分隔的经纬度
                    coordString = tmpList[i]['location']
                    coordList = coordString.split(',')
                    # 放入结果序列
                    resultList.append((float(coordList[0]),float(coordList[1])))
                except:
                    # 如果发生错误则存入None
                    resultList.append(None)
            return resultList
        elif answer['info'] == 'DAILY_QUERY_OVER_LIMIT':
            # 4.2-当前账号的余额用完了,返回-1
            return -1
        else:
            # 4.3-如果发生其他错误则返回-2
            return -2
    else:
        return -3

# 检查是否登录
def check_login_status():
    login_status = False
    if session.get('user_id') is not None:
        login_status = True
    return login_status


class LoginStatusDictionary:
    login_status_dictionary = {}

    def __init__(self):
        users_in_db = User.query.filter(User.role == 0).all()
        for each_user in users_in_db:
            self.login_status_dictionary[str(each_user.id)] = 0

    def login_status_update(self, user_id):
        self.login_status_dictionary[str(user_id)] = 1

    def logout_status_update(self, user_id):
        self.login_status_dictionary[str(user_id)] = 0

    def register_success(self, user_id):
        self.login_status_dictionary[str(user_id)] = 0

    def login_permission(self, user_id):
        if self.login_status_dictionary[str(user_id)] == 1:
            return False
        else:
            return True


def get_available_time(available_time):
    time = available_time.split('-')
    available_weekday = weekday[time[0]]
    available_start_time = time[1]
    available_end_time = time[2]
    return available_weekday, available_start_time, available_end_time


def get_house_number():
    new_house_in_db = NewHouse.query.filter().all()
    second_hand_house_in_db = SecondHouse.query.filter().all()
    publish_in_db = Publish.query.filter().all()
    return len(new_house_in_db), len(second_hand_house_in_db), len(publish_in_db)-1


# 用来判断用户的登陆状态，
# 如果用户尚未登录，返回-1
# 如果以customer状态登录，返回0
# 如果以admin状态登录，返回1
def get_session_role():
    session_role = '-1'
    if 'role' in session.keys():
        session_role = session.get('role')
    return session_role


def pinyin(Chinese):
    char_list = lazy_pinyin(Chinese)
    for i in range(len(char_list)):
        char_list[i]=char_list[i].capitalize()
    return " ".join(char_list)


def verify_new_house_input(house_name, room, size, province, city, district, price_each_square_meter, start_end_hour, position):
    verification = 0
    if house_name == '' or room == '' or size == '' or province == '' or city == '' or district == '' or \
            price_each_square_meter == '' or start_end_hour == '' or position == '':
        verification = -1
        return verification
    if '-' not in str(start_end_hour):
        verification = -2
        return verification
    if len(str(start_end_hour).split('-')) != 2:
        verification = -3
        return verification
    if not str(price_each_square_meter).isdigit() or not str(size).isdigit() or not str(room).isdigit() or\
            not str(start_end_hour).split('-')[0].isdigit() or not str(start_end_hour).split('-')[1].isdigit():
        verification = -4
        return verification
    if not int(str(start_end_hour).split('-')[0]) < int(str(start_end_hour).split('-')[1]):
        verification = -5
        return verification
    if not 0 <= int(str(start_end_hour).split('-')[0]) <= 24 or not 0 <= int(str(start_end_hour).split('-')[1]) <= 24:
        verification = -6
        return verification
    if ExcuteSingleQuery([position]) == -1 or ExcuteSingleQuery([position]) == -2 or ExcuteSingleQuery([position]) == -3:
        verification = -7
        return verification
    return verification


def verify_second_hand_house_input(house_name, size, province, city, price_each_square_meter, start_end_hour, position):
    verification = 0
    if house_name == '' or size == '' or province == '' or city == '' or position == '' or \
            price_each_square_meter == '' or start_end_hour == '':
        verification = -1
        return verification
    if '-' not in str(start_end_hour):
        verification = -2
        return verification
    if len(str(start_end_hour).split('-')) != 2:
        verification = -3
        return verification
    if not str(price_each_square_meter).isdigit() or not str(size).isdigit() or \
            not str(start_end_hour).split('-')[0].isdigit() or not str(start_end_hour).split('-')[1].isdigit():
        verification = -4
        return verification
    if not int(str(start_end_hour).split('-')[0]) < int(str(start_end_hour).split('-')[1]):
        verification = -5
        return verification
    if not 0 <= int(str(start_end_hour).split('-')[0]) <= 24 or not 0 <= int(str(start_end_hour).split('-')[1]) <= 24:
        verification = -6
        return verification
    if ExcuteSingleQuery([position]) == -1 or ExcuteSingleQuery([position]) == -2 or ExcuteSingleQuery([position]) == -3:
        verification = -7
        return verification
    return verification


def verify_modify_house_info(price_each_square_meter, start_end_hour):
    verification = 0
    if not str(price_each_square_meter).isdigit():
        verification = -1
        return verification
    if '-' not in str(start_end_hour):
        verification = -2
        return verification
    if len(str(start_end_hour).split('-')) != 2:
        verification = -3
        return verification
    if not str(start_end_hour).split('-')[0].isdigit() or not str(start_end_hour).split('-')[1].isdigit():
        verification = -4
        return verification
    if not int(str(start_end_hour).split('-')[0]) < int(str(start_end_hour).split('-')[1]):
        verification = -5
        return verification
    if not 0 <= int(str(start_end_hour).split('-')[0]) <= 24 or not 0 <= int(str(start_end_hour).split('-')[1]) <= 24:
        verification = -6
        return verification
    return verification


def get_api_feedback(query, address, room, size):
    addr = ExcuteSingleQuery([address])
    # print(addr)
    if addr[0] is not None and addr!= -1 and addr != -2 and addr != -3:
        longitude = addr[0][0]
        latitude = addr[0][1]
        output, low, high, accuracy = price_model_predict(query, longitude, latitude, room, size)

        feedback = {
            'longitude': longitude,
            'latitude': latitude,
            'predicted_house_price': output,
        }
        return json.dumps(feedback)

    else:
        feedback = {'error': 'token verification error'}
        return json.dumps(feedback)

def price_model_predict(query, longitude, latitude, room, size):

    if query == '0':
        # 北京

        if (longitude > 115.25 and longitude < 117.3 and latitude > 39.26 and latitude < 41.03):
            model = pickle.load(open('./estateApp/ml/new house models/new_house_model_1.pkl', 'rb'))
            float_features = []
            float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 3941.94
            hi = 5481.29
            accuracy = 0.6786
        # 天津 & 江苏 & 上海
        elif ((longitude > 116.43 and longitude < 118.194 and latitude > 38.34 and latitude < 40.15) or
              (longitude > 116.18 and longitude < 121.57 and latitude > 30.45 and latitude < 35.20) or
              (longitude > 120.51 and longitude < 122.12 and latitude > 30.40 and latitude < 31.53)):
            model = pickle.load(open('./estateApp/ml/new house models/new_house_model_2.pkl', 'rb'))
            float_features = []
            float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 2073.82
            hi = 1824.29
            accuracy = 0.6750
        # 浙江 & 福建 & 广东
        elif ((longitude > 118 and longitude < 123 and latitude > 27.12 and latitude < 31.31) or
              (longitude > 115.50 and longitude < 120.40 and latitude > 23.30 and latitude < 28.22) or
              (longitude > 109.45 and longitude < 117.20 and latitude > 20.12 and latitude < 25.31)):
            model = pickle.load(open('./estateApp/ml/new house models/new_house_model_3.pkl', 'rb'))
            float_features = []
            float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 2073.82
            hi = 1824.29
            accuracy = 0.6750

        # 吉林  & 辽宁 & 内蒙古  & 宁夏 & 陕西 & 湖北 & 重庆 & 湖南
        elif ((longitude > 121.38 and longitude < 131.19 and latitude > 40.52 and latitude < 46.18) or
              (longitude > 118.53 and longitude < 125.46 and latitude > 38.43 and latitude < 43.26) or
              (longitude > 97.12 and longitude < 126.04 and latitude > 53.23 and latitude < 37.24) or
              (longitude > 104.17 and longitude < 107.39 and latitude > 35.14 and latitude < 39.23) or
              (longitude > 105.29 and longitude < 111.15 and latitude > 31.42 and latitude < 39.35) or
              (longitude > 108.21 and longitude < 116.07 and latitude > 29.05 and latitude < 33.20) or
              (longitude > 105.17 and longitude < 110.11 and latitude > 28.10 and latitude < 32.13) or
              (longitude > 108.47 and longitude < 114.15 and latitude > 24.38 and latitude < 30.8)):
            model = pickle.load(open('./estateApp/ml/new house models/new_house_model_4.pkl', 'rb'))
            float_features = []
            float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 1890.82
            hi = 1514.51
            accuracy = 0.7509

        else:
            model = pickle.load(open('./estateApp/ml/new house models/new_house_model_5.pkl', 'rb'))
            float_features = []
            float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 1498.33
            hi = 1266.85
            accuracy = 0.6027


    else:
        # 北京
        if (longitude > 115.25 and longitude < 117.3 and latitude > 39.26 and latitude < 41.03):
            model = pickle.load(open('./estateApp/ml/second hand house models/second_hand_house_model_1.pkl', 'rb'))
            float_features = []
            # float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 5795.75
            hi = 5317.77
            accuracy = 0.7117
        # 天津 & 江苏 & 上海
        elif ((longitude > 116.43 and longitude < 118.194 and latitude > 38.34 and latitude < 40.15) or
              (longitude > 116.18 and longitude < 121.57 and latitude > 30.45 and latitude < 35.20) or
              (longitude > 120.51 and longitude < 122.12 and latitude > 30.40 and latitude < 31.53)):
            model = pickle.load(open('./estateApp/ml/second hand house models/second_hand_house_model_2.pkl', 'rb'))
            float_features = []
            # float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 1280.91
            hi = 1135.05
            accuracy = 0.8048

        # 浙江 & 福建 & 广东
        elif ((longitude > 118 and longitude < 123 and latitude > 27.12 and latitude < 31.31) or
              (longitude > 115.50 and longitude < 120.40 and latitude > 23.30 and latitude < 28.22) or
              (longitude > 109.45 and longitude < 117.20 and latitude > 20.12 and latitude < 25.31)):
            model = pickle.load(open('./estateApp/ml/second hand house models/second_hand_house_model_3.pkl', 'rb'))
            float_features = []
            # float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 875.23
            hi = 726.26
            accuracy = 0.7865

        # 吉林  & 辽宁 & 内蒙古  & 宁夏 & 陕西 & 湖北 & 重庆 & 湖南
        elif ((longitude > 121.38 and longitude < 131.19 and latitude > 40.52 and latitude < 46.18) or
              (longitude > 118.53 and longitude < 125.46 and latitude > 38.43 and latitude < 43.26) or
              (longitude > 97.12 and longitude < 126.04 and latitude > 53.23 and latitude < 37.24) or
              (longitude > 104.17 and longitude < 107.39 and latitude > 35.14 and latitude < 39.23) or
              (longitude > 105.29 and longitude < 111.15 and latitude > 31.42 and latitude < 39.35) or
              (longitude > 108.21 and longitude < 116.07 and latitude > 29.05 and latitude < 33.20) or
              (longitude > 105.17 and longitude < 110.11 and latitude > 28.10 and latitude < 32.13) or
              (longitude > 108.47 and longitude < 114.15 and latitude > 24.38 and latitude < 30.8)):
            model = pickle.load(open('./estateApp/ml/second hand house models/second_hand_house_model_4.pkl', 'rb'))
            float_features = []
            # float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 587.79
            hi = 613.73
            accuracy = 0.7695

        else:
            model = pickle.load(open('./estateApp/ml/second hand house models/second_hand_house_model_5.pkl', 'rb'))
            float_features = []
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longitude)
            lo = 550.66
            hi = 611.48
            accuracy = 0.7842

    final_features = [np.array(float_features)]
    prediction = model.predict(final_features)
    output = round(prediction[0], 2)  # 保留小数点后两位

    return output, round(output - lo, 2), round(output + hi, 2), accuracy


def get_model_type(longitude, latitude):
    type = 0
    return type

