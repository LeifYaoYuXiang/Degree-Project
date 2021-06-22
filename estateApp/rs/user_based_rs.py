from math import *
import csv
import os
import random
from estateApp.models import NewHouse, SecondHouse, Publish, User


def generate_random_list(lower, higher, number):
    house_index = []
    for i in range(number):
        random_number = random.randint(lower, higher)
        while random_number not in house_index:
            house_index.append(random_number)
    return house_index


def generate_random_house_info(house_type, limit_number=8):
    house_index = generate_random_list(1, 2000, limit_number)
    house_info = []
    if int(house_type) == 0:
        for i in range(len(house_index)):
            each_house_in_db = NewHouse.query.filter(NewHouse.index == house_index[i]).first()
            img_num = str(int(each_house_in_db.index) % 210)
            image_url = 'image/' + img_num + '.jpg'
            related_publish = Publish.query.filter(Publish.house_id == each_house_in_db.index).first()
            related_house_inspector_id = related_publish.house_inspector_id
            house_inspector = User.query.filter(User.id == related_house_inspector_id).first()
            house_info.append({
                'id': 'New'+str(each_house_in_db.index),
                'image_url': image_url,
                'house_name': each_house_in_db.house_name,
                'address': each_house_in_db.position,
                'price': each_house_in_db.price_each_square_meter,
                'user_id': related_house_inspector_id,
                'house_inspector_name': each_house_in_db.city,
            })
    else:
        for i in range(len(house_index)):
            each_house_in_db = SecondHouse.query.filter(SecondHouse.index == house_index[i]).first()
            img_num = str(int(each_house_in_db.index) % 210)
            image_url = 'image/' + img_num + '.jpg'
            related_publish = Publish.query.filter(Publish.house_id == each_house_in_db.index).first()
            related_house_inspector_id = related_publish.house_inspector_id
            house_inspector = User.query.filter(User.id == related_house_inspector_id).first()
            house_info.append({
                'id': 'Second'+str(each_house_in_db.index),
                'image_url': image_url,
                'house_name': each_house_in_db.house_name,
                'address': each_house_in_db.position,
                'price': each_house_in_db.price_each_square_meter,
                'user_id': related_house_inspector_id,
                'house_inspector_name': each_house_in_db.city,
            })
    return house_info


class UserBasedHouseRecommendationSystem:
    new_house_rating_data = {}
    second_hand_house_rating_data = {}
    currentDir = os.getcwd()
    new_house_csv_path = os.path.join(currentDir, 'estateApp', 'rs', 'new_house_rating.csv')
    second_house_csv_path = os.path.join(currentDir, 'estateApp', 'rs', 'second_hand_house_rating.csv')

    def __init__(self):
        content = []
        with open(self.new_house_csv_path, encoding='utf-8') as fp:
            content = fp.readlines()
        for line in content[1:len(content)]:
            line = line.strip().split(',')
            if not line[0] in self.new_house_rating_data.keys():
                self.new_house_rating_data[line[0]] = {line[1]: line[2]}
            else:
                self.new_house_rating_data[line[0]][line[1]] = line[2]

        content = []
        with open(self.second_house_csv_path, encoding='utf-8') as fp:
            content = fp.readlines()
        for line in content[1:len(content)]:
            line = line.strip().split(',')
            if not line[0] in self.second_hand_house_rating_data.keys():
                self.second_hand_house_rating_data[line[0]] = {line[1]: line[2]}
            else:
                self.second_hand_house_rating_data[line[0]][line[1]] = line[2]

    def euclidean(self, user1, user2, house_type):
        if int(house_type) == 0:
            user1_data = self.new_house_rating_data[user1]
            user2_data = self.new_house_rating_data[user2]
        else:
            user1_data = self.second_hand_house_rating_data[user1]
            user2_data = self.second_hand_house_rating_data[user2]
        distance = 0
        for key in user1_data.keys():
            if key in user2_data.keys():
                distance += pow(float(user1_data[key]) - float(user2_data[key]), 2)
        return 1 / (1 + sqrt(distance))

    def top_10_similar(self, user_id, house_type):
        res = []
        if int(house_type) == 0:
            data = self.new_house_rating_data
        else:
            data = self.second_hand_house_rating_data
        for userid in data.keys():
            if not userid == user_id:
                similar = self.euclidean(user_id, userid, house_type)
                res.append((userid, similar))
        res.sort(key=lambda val: val[1])
        return res[:4]

    # 0为新房
    # 1为二手房
    def recommend(self, user_id, house_type, limit_number=8):
        top_sim_user = self.top_10_similar(str(user_id), house_type)[0][0]
        if int(house_type) == 0:
            data = self.new_house_rating_data
        else:
            data = self.second_hand_house_rating_data
        items = data[top_sim_user]
        recommendations = []
        house_info = []
        for item in items.keys():
            recommendations.append((item, items[item]))
        recommendations.sort(key=lambda val: val[1], reverse=True)

        if int(house_type) == 0:
            for i in range(len(recommendations[:limit_number])):
                each_house = recommendations[i]
                each_house_in_db = NewHouse.query.filter(NewHouse.index == each_house[0]).first()
                img_num = str(int(each_house_in_db.index) % 210)
                image_url = 'image/' + img_num + '.jpg'
                related_publish = Publish.query.filter(Publish.house_id == each_house_in_db.index).first()
                related_house_inspector_id = related_publish.house_inspector_id
                house_inspector = User.query.filter(User.id == related_house_inspector_id).first()
                house_info.append({
                    'id': 'New' + str(each_house_in_db.index),
                    'image_url': image_url,
                    'house_name': each_house_in_db.house_name,
                    'address': each_house_in_db.position,
                    'price': each_house_in_db.price_each_square_meter,
                    'user_id': related_house_inspector_id,
                    'house_inspector_name': each_house_in_db.city,
                })
        else:
            for i in range(len(recommendations[:limit_number])):
                each_house = recommendations[i]
                each_house_in_db = SecondHouse.query.filter(SecondHouse.index == each_house[0]).first()
                img_num = str(int(each_house_in_db.index) % 210)
                image_url = 'image/' + img_num + '.jpg'
                related_publish = Publish.query.filter(Publish.house_id == each_house_in_db.index).first()
                related_house_inspector_id = related_publish.house_inspector_id
                house_inspector = User.query.filter(User.id == related_house_inspector_id).first()
                house_info.append({
                    'id': 'Second' + str(each_house_in_db.index),
                    'image_url': image_url,
                    'house_name': each_house_in_db.house_name,
                    'address': each_house_in_db.position,
                    'price': each_house_in_db.price_each_square_meter,
                    'user_id': related_house_inspector_id,
                    'house_inspector_name': each_house_in_db.city,
                })

        return house_info

    def update(self, house_type, house_id, user_id, house_rating):
        if int(house_type) == 0:
            if user_id in self.new_house_rating_data.keys():
                self.new_house_rating_data[user_id][house_id] = house_rating
            else:
                self.new_house_rating_data[user_id] = {
                    house_id: house_rating
                }
            rating_fields = [int(user_id), int(house_id), house_rating]
            with open(self.new_house_csv_path, 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(rating_fields)
                f.close()
        else:
            if user_id in self.second_hand_house_rating_data.keys():
                self.second_hand_house_rating_data[user_id][house_id] = house_rating
            else:
                self.second_hand_house_rating_data[user_id] = {
                    house_id: house_rating
                }
            rating_fields = [int(user_id), int(house_id), house_rating]
            with open(self.second_house_csv_path, 'a', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(rating_fields)
                f.close()

    def check_new_house_rating_status(self, user_id):
        if str(user_id) in self.new_house_rating_data.keys():
            return True
        else:
            return False

    def check_second_hand_rating_status(self, user_id):
        if str(user_id) in self.second_hand_house_rating_data.keys():
            return True
        else:
            return False

    def check_rating_status(self, user_id, house_id, house_type):
        if int(house_type) == 0:
            if user_id in self.new_house_rating_data.keys():
                if house_id in self.new_house_rating_data[user_id]:
                    return self.new_house_rating_data[user_id][house_id]
                else:
                    return -1
            else:
                return -1
        else:
            if user_id in self.second_hand_house_rating_data.keys():
                if house_id in self.second_hand_house_rating_data[user_id]:
                    return self.second_hand_house_rating_data[user_id][house_id]
                else:
                    return -1
            else:
                return -1
