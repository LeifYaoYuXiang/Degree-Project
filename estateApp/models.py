from estateApp import db


# 使用者，包括 customers和house inspectors
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    phone = db.Column(db.String(11))
    emails = db.Column(db.String(30))
    role = db.Column(db.Integer)  # 表示职介， 0代表Customers， 1代表house_inspector
    password = db.Column(db.String(64))
    # Foreign keys
    appointments = db.relationship('Appointment', backref='customer', lazy='dynamic')
    messages = db.relationship('Message', backref='sender', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.id)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 外键
    house_inspector_user_id = db.Column(db.Integer)
    content = db.Column(db.String(64))
    replied_content = db.Column(db.String(64))

    message_year = db.Column(db.Integer)
    message_month = db.Column(db.Integer)
    message_date = db.Column(db.Integer)

    replied_year = db.Column(db.Integer)
    replied_month = db.Column(db.Integer)
    replied_date = db.Column(db.Integer)

    status = db.Column(db.Integer, default=0)  # 0代表尚未回复， 1代表已经回复

    def __repr__(self):
        return '<Message {}>'.format(self.id)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 外键
    house_inspector_user_id = db.Column(db.Integer)
    house_id = db.Column(db.Integer)
    content = db.Column(db.String(64))
    house_type = db.Column(db.Integer)  # 判定house是新房还是二手房，新房：0 二手房： 1
    appointment_year = db.Column(db.Integer)
    appointment_month = db.Column(db.Integer)
    appointment_date = db.Column(db.Integer)

    status = db.Column(db.Integer, default=0)  # 0代表尚未确认， 1代表已经确认

    def __repr__(self):
        return '{}-{}-{}'.format(self.appointment_year, self.appointment_month, self.appointment_date)


class NewHouse(db.Model):
    index = db.Column(db.Integer, primary_key=True)
    province = db.Column(db.String(64))
    city = db.Column(db.String(64))
    house_name = db.Column(db.String(64))
    room = db.Column(db.String(64))
    size = db.Column(db.String(64))
    position = db.Column(db.String(128))
    district = db.Column(db.String(64))
    price_each_square_meter = db.Column(db.Integer)
    latitude = db.Column(db.Float)
    longtitude = db.Column(db.Float)


class SecondHouse(db.Model):
    index = db.Column(db.Integer, primary_key=True)
    province = db.Column(db.String(64))
    city = db.Column(db.String(64))
    house_name = db.Column(db.String(64))
    position = db.Column(db.String(128))
    total_price = db.Column(db.String(64))
    price_each_square_meter = db.Column(db.Integer)
    size = db.Column(db.Integer)
    latitude = db.Column(db.Float)
    longtitude = db.Column(db.Float)


class Publish(db.Model):
    index = db.Column(db.Integer, primary_key=True)
    house_type = db.Column(db.Integer)  # 判定house是新房还是二手房，新房：0 二手房： 1
    house_id = db.Column(db.Integer)
    house_inspector_id = db.Column(db.Integer)
    available_time = db.Column(db.String(64))


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    room_number_preference = db.Column(db.Integer, default=0)
    size_preference = db.Column(db.Integer, default=0)
