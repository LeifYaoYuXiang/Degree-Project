from estateApp.models import NewHouse, SecondHouse, Publish, User


def get_item_from_locality(house_type, province, city, limit_number):
    house_info = []
    if int(house_type) == 0:
        houses_in_db = NewHouse.query.filter(NewHouse.province == province, NewHouse.city == city).limit(limit_number)
        for each_house_in_db in houses_in_db:
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
        house_in_db = SecondHouse.query.filter(SecondHouse.province == province, SecondHouse.city == city).limit(limit_number)
        for each_house_in_db in house_in_db:
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
    return house_info
