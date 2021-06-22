# -*- coding: utf-8 -*-
# python3.7
from urllib import parse
import requests

url = 'http://39.102.48.55:3389/price_p'

# :
##
# args:
#   query: String format, which means that whether the house is one new house or one second-hand house,
#   0 means it is one new house, 1 means it is one second hand house
#   address: String format, which means the address which should be in Chinese
#   room_num: String format, which means the number of rooms
#   size: String format, which means the size of the house
##
# 验证输入格式是否规范
def input_inspect(query, address, room_num, size):
    if query != '0' and query != '1':
        return 'The first parameter has a format error'
    elif isinstance(address, int):
        return 'The second parameter has a format error'
    elif not room_num.isdigit():
        return 'The third parameter has a format error'
    elif not size.isdigit():
        return 'The fourth parameter has a format error'
    else:
        return True


##
# args
#   token: the developer's token
#   user_id: the developer's user_id
##
def prediction(query, address, room_num, size, token, user_id):
    # 请求的header
    headers = {'Content-Type': 'application/x-www-form-urlencoded',
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0'}
    # 请求参数
    if input_inspect(query, address, room_num, size) is True:
        data = {
            'user_id': user_id,
            'query': query,
            'address': address,
            'room_num': room_num,
            'size': size,
            'token': token,
        }
        # 对请求参数进行encode
        data = parse.urlencode(data)
        result = requests.post(url, headers=headers, data=data)
        print("the prediction result is:", result.text)
    else:
        print(input_inspect(query, address, room_num, size))


if __name__ == '__main__':
    user_id = '5'
    token = 'MTYxODI5MDE5NS42OTIyMjcxOmIxMzMzYjk5NWM3MjVjMGQ4ZjVlYzVjMmQ4YTM2NDRlMzhjM2M1NGM='
    prediction('0', '北京市朝阳区北京工业大学', '5', '100', user_id=user_id, token=token)


