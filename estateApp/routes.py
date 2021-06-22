# basic library
import re
import sys
import random
import datetime

# Flask
from flask import render_template, redirect, url_for, request, session, flash, send_from_directory
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from estateApp import app, db, Config
from estateApp.forms import SearchHouseForm, RegisterForm, LoginForm, ContactForm, AppointmentForm, ReplyForm, \
    AppointmentReadForm, AppointmentUnReadForm, PublishNewHouseForm, PublishSecondHandHouseForm, ModifyHouseInfoForm
from estateApp.models import User, Message, Appointment, NewHouse, SecondHouse, Publish
from estateApp.utils import check_login_status, LoginStatusDictionary, get_available_time, get_house_number, \
    get_session_role, verify_new_house_input, verify_second_hand_house_input, verify_modify_house_info, category_price, \
    get_api_feedback, pinyin, price_model_predict

from estateApp.token import generate_token, certify_token
from estateApp.rs.item_based_rs import get_item_from_locality

# Ajax | json
import json
from flask import jsonify

# 头像
from flask_avatars import Avatars
import hashlib

avatars = Avatars(app)

# 后台分页查询
from flask_paginate import Pagination, get_page_args, get_page_parameter

# IR 搜索
from estateApp.utils import ExcuteSingleQuery as esq
from estateApp.ir.query import Query
from estateApp.ir.query_new_house import QueryNew
from estateApp.ir.query_second_house import QuerySecond

sys.path.append('..')
# 新闻cache:(key:id value:content)
newsContent_dict = {}

# ML 预测
import numpy as np
import pickle

model = ''

# 推荐系统
from estateApp.rs.user_based_rs import UserBasedHouseRecommendationSystem, generate_random_house_info

UserBasedHouseRecommendationSystem = UserBasedHouseRecommendationSystem()

# 一些方法
# login_status_dictionary = LoginStatusDictionary()
new_house_number, second_hand_house_number, publish_index = get_house_number()

# Demo 查看针对某一个user的针对某一个house的评分
# print(UserBasedHouseRecommendationSystem.check_rating_status(user_id=6, house_id=100, house_type=1))

house_ajax_list = list()


@app.route('/', methods=['GET', 'POST'])
# 主页： Customer & House Inspector
@app.route('/index', methods=['GET', 'POST'])
def index():
    search_house_form = SearchHouseForm()
    login_status = check_login_status()
    session_role = get_session_role()
    if search_house_form.submit.data:
        search_query = search_house_form.house_info.data
        # 搜索关键词，返回在 新房&二手房 范围内的结果
        if search_query is not None:
            return redirect(url_for('search_result', types=0, query=search_query))
        # 直接点击search，无关键词，返回全部 新房&二手房
        else:
            return redirect(url_for('search_result', types=0))
    # 新房与二手房的推荐系统
    if not login_status:
        new_house_info = generate_random_house_info(house_type=0, limit_number=8)
        second_house_info = generate_random_house_info(house_type=1, limit_number=8)
    else:
        user_id = session['user_id']
        if UserBasedHouseRecommendationSystem.check_new_house_rating_status(user_id=user_id):
            new_house_info = UserBasedHouseRecommendationSystem.recommend(user_id=user_id, house_type=0)
        else:
            new_house_info = generate_random_house_info(house_type=0, limit_number=8)

        if UserBasedHouseRecommendationSystem.check_second_hand_rating_status(user_id=user_id):
            second_house_info = UserBasedHouseRecommendationSystem.recommend(user_id=user_id, house_type=1)
        else:
            second_house_info = generate_random_house_info(house_type=1, limit_number=8)

    # house inspector的界面
    house_inspector_list = []
    all_house_inspector_in_db = User.query.filter(User.role == 1).all()
    for each_house_inspector in all_house_inspector_in_db:
        img_num = str(each_house_inspector.id % 10)
        image_url = 'front_end/img/team/0' + img_num + '.jpg'
        house_inspector_list.append({
            'id': each_house_inspector.id,
            'image_url': image_url,
            'name': each_house_inspector.name,
            'phone': each_house_inspector.phone
        })

    # 随机推荐
    q = Query('./estateApp/ir/index')
    res = q.standard_search('北京')
    # 存入缓存
    for item in res:
        if item['id'] not in newsContent_dict.keys():
            newsContent_dict[item['id']] = item
    result_list = []
    res = random.choices(res, k=3)
    # 存储返回前端数据
    for item in res:
        num = random.randint(1, 7)
        it = []
        url = "../static/front_end/img/blog/0" + str(num) + ".jpg"
        it.append(url)
        # it.append(item)
        it.append(item['id'])
        it.append(item['title'])
        it.append(item['time'])
        result_list.append(it)
    # 添加session为展示侧边栏使用
    if (len(result_list) >= 3):
        session['result_list'] = result_list[:3]
    else:
        session['result_list'] = result_list

    return render_template('index.html', search_house_form=search_house_form, login_status=login_status,
                           house_inspector_list=house_inspector_list, new_house_info=new_house_info,
                           second_house_info=second_house_info, session_role=session_role, house_info_list=result_list)


# 登录页面 -> 姚宇翔
@app.route('/login', methods=['GET', 'POST'])
def login():
    global user_status
    session.clear()
    login_form = LoginForm()
    if login_form.submit.data:
        login_name = login_form.name.data
        login_password = login_form.password.data
        user_in_db = User.query.filter(User.name == login_name).first()
        if user_in_db is not None:
            user_role = user_in_db.role
            if user_role == 0:
                # 是 Customer
                if check_password_hash(user_in_db.password, login_password):
                    # 登陆成功
                    session['user_id'] = user_in_db.id
                    session['user_name'] = user_in_db.name
                    # user_status = 0
                    session['role'] = 0
                    return redirect(url_for('index'))
                else:
                    flash('Login Fail. Please Check Your Password')
            else:
                # 是 House Inspector
                if user_in_db.password == login_password:
                    session['user_id'] = user_in_db.id
                    session['user_name'] = user_in_db.name
                    session['role'] = 1
                    return redirect(url_for('personal_page_staff'))
                else:
                    flash('Login Fail. Please Check Your Password')
        else:
            flash('Login Fail. Please Check Your Username')
    return render_template('login.html', login_form=login_form)


# 注册页面 -> 姚宇翔
@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.submit.data:
        register_name = register_form.name.data
        register_password = register_form.password.data
        register_email = register_form.email.data
        register_phone = register_form.phone.data
        if register_name is not None and register_password is not None:
            user_in_db = User.query.filter(User.name == register_name).first()
            if user_in_db is None:
                user_registered = User(
                    name=register_name,
                    password=generate_password_hash(register_password),
                    emails=register_email,
                    phone=register_phone,
                    role=0,
                )
                db.session.add(user_registered)
                db.session.commit()
                return redirect(url_for('login'))
            else:
                flash('Username has already registered')
        else:
            flash('Please check your input name and password')
    return render_template('register.html', register_form=register_form)


# 搜索结果展示 -> 倪莎
@app.route('/search_result/<types>/', methods=['GET', 'POST'])
# @app.route('/search_result/<types>/<query>', methods=['GET', 'POST'])
@app.route('/search_result/<types>/<filter>', methods=['GET', 'POST'])
@app.route('/search_result/<types>/<filter>/<query>', methods=['GET', 'POST'])
def search_result(types, query=None, filter=0):
    session_role = get_session_role()
    login_status = check_login_status()
    # 区分 新房：1 / 二手房：2 / 新房+二手房：0
    # 获得房产搜索 List
    if types == '1':
        title_content = 'new house'
        result_house_list = generate_search_result_list('1', query, filter)

    elif types == '2':
        title_content = '2nd hand house'
        result_house_list = generate_search_result_list('2', query, filter)
    else:
        title_content = 'House'
        result_house_list_1 = generate_search_result_list('1', query, filter)
        result_house_list_2 = generate_search_result_list('2', query, filter)
        result_house_list = result_house_list_1 + result_house_list_2
    # 获得分页对象
    pagination = generate_search_result_pagination(len(result_house_list), title_content)
    #    if query is None:
    #        result_house_list= result_house_list[:48]

    # 房产搜索结果展示
    search_house_form = SearchHouseForm()
    if search_house_form.validate_on_submit():
        query = search_house_form.house_info.data
        return redirect(url_for('search_result', types=types, filter=filter, query=query))
    # 房产筛选
    data = request.form.get('data')
    if data:
        x = json.dumps(data)

    # 渲染页面
    return render_template('search_result.html', title_content=title_content,
                           login_status=login_status,
                           result_house_list=result_house_list,
                           pagination=pagination,
                           search_house_form=search_house_form,
                           session_role=session_role,
                           search_query=session["search_query"],
                           types=types,
                           filter=filter)


# 房间信息展示 -> 于佳悦
@app.route('/house_item/<id>', methods=['GET', 'POST'])
def house_item(id):
    login_status = check_login_status()
    session_role = get_session_role()

    house_type = (re.findall(r"[a-zA-Z]+", id))[0]  # 匹配New或者Second
    house_id = (re.findall(r"\d+", id))[0]  # 匹配house id
    if house_type == 'New':
        house_in_db = NewHouse.query.filter(NewHouse.index == house_id).first()
        publish = Publish.query.filter(Publish.house_id == house_id, Publish.house_type == 0).first()
        house_size = house_in_db.size
        # house_size = re.findall(r"\d+", house_size)[0] + ' ㎡' + ' - ' + re.findall(r"\d+", house_size)[1] + '  ㎡'
        house_room = house_in_db.room
    else:
        house_in_db = SecondHouse.query.filter(SecondHouse.index == house_id).first()
        publish = Publish.query.filter(Publish.house_id == house_id, Publish.house_type == 1).first()
        house_room = '¥ ' + str(format(int(house_in_db.total_price) * 10000, ","))
        house_size = str(house_in_db.size) + ' ㎡'
    house_inspector = User.query.filter(User.id == publish.house_inspector_id).first()
    inspector_id = house_inspector.id
    inspector_name = house_inspector.name
    inspector_phone = house_inspector.phone
    house_id = int(house_id)
    price = house_in_db.price_each_square_meter
    price = str(format(price, ","))  # 给价格加上千位分隔逗号
    house_district = house_in_db.position
    if house_in_db.province == 'Zhi Xia Shi':
        house_city = house_in_db.city
    else:
        house_city = house_in_db.province + ' / ' + house_in_db.city
    available_time = get_available_time(publish.available_time)[
                         1] + ':00 - ' + get_available_time(publish.available_time)[2] + ':00 ' + ' ' + \
                     get_available_time(publish.available_time)[0] + ' '
    house_name = house_in_db.house_name
    house_type_num = publish.house_type

    appointment_form = AppointmentForm()
    user_id = session.get("user_id")

    # 评分
    if login_status:
        rating = UserBasedHouseRecommendationSystem.check_rating_status(user_id=str(user_id), house_id=str(house_id),
                                                                        house_type=str(house_type_num))
    else:
        rating = -1

    recommendation_house = get_item_from_locality(house_type=0, province=house_in_db.province,
                                                  city=house_in_db.city, limit_number=8)
    if appointment_form.validate_on_submit():
        if login_status:
            time = appointment_form.time.data
            message = appointment_form.message.data
            appointment = Appointment(
                content=message,
                customer_user_id=user_id,
                house_inspector_user_id=house_inspector.id,
                house_id=house_id,
                house_type=house_type_num,
                appointment_year=int(str(time)[0:4]),
                appointment_month=int(str(time)[5:7]),
                appointment_date=int(str(time)[8:10])
            )
            db.session.add(appointment)
            db.session.commit()
            return redirect(url_for('personal_page'))
        else:
            return redirect(url_for('login'))

    if house_type_num == 0:
        house_type = 'New House'
    else:
        house_type = 'Second Hand house'

    # 获取星期对应数字
    week_number = int((publish.available_time)[0])
    if week_number == 7:
        week_number = 0

    return render_template('house_item.html',
                           house_id=house_id,
                           inspector_id=inspector_id,
                           inspector_name=inspector_name,
                           inspector_phone=inspector_phone,
                           price=price,
                           house_district=house_district,
                           house_city=house_city,
                           house_room=house_room,
                           house_size=house_size,
                           house_name=house_name,
                           house_type_num=house_type_num,
                           house_type=house_type,
                           available_time=available_time,
                           appointment_form=appointment_form,
                           login_status=login_status,
                           recommendation_house=recommendation_house,
                           week_number=week_number,
                           session_role=session_role,
                           rating=rating)


# 售房经理信息列表展示 -> 倪莎
@app.route('/house_inspector_list/', methods=['GET', 'POST'])
def house_inspector_list():
    # 中介信息展示 - 真正数据传入展示
    login_status = check_login_status()
    session_role = get_session_role()
    house_inspector_list_temp = User.query.filter(User.role == 1).all()
    house_inspector_list = []
    for hi in house_inspector_list_temp:
        hi_id = hi.id
        img_num = str(hi_id % 10)
        image_url = 'front_end/img/team/0' + img_num + '.jpg'
        name = hi.name
        tel = hi.phone
        house_inspector_item_temp = {'id': hi_id, 'image_url': image_url, 'name': name, 'tel': tel}
        house_inspector_list.append(house_inspector_item_temp)
    return render_template('house_inspector_list.html',
                           house_inspector_list=house_inspector_list,
                           login_status=login_status, session_role=session_role)


# 售房经理信息单栏展示 -> 于佳悦
@app.route('/house_inspector_item/<id>', methods=['GET', 'POST'])
def house_inspector_item(id):
    session_role = get_session_role()
    login_status = check_login_status()
    contact_form = ContactForm()
    house_inspector = User.query.filter(User.id == id).first()
    inspector_img = 'front_end/img/team/0' + id + '.jpg'
    inspector_name = house_inspector.name
    inspector_phone = house_inspector.phone
    inspector_email = house_inspector.emails

    if contact_form.validate_on_submit():
        if login_status:
            content = contact_form.content.data
            today = datetime.date.today()
            message = Message(content=content, customer_user_id=session.get("user_id"),
                              house_inspector_user_id=id,
                              message_year=int(str(today)[0:4]),
                              message_month=int(str(today)[5:7]),
                              message_date=int(str(today)[8:10]))
            db.session.add(message)
            db.session.commit()
            return redirect(url_for('personal_page'))
        else:
            flash('Please login first')
            return redirect(url_for('login'))

    # 分页
    r = db.session.query(NewHouse).join(Publish, Publish.house_id == NewHouse.index).filter(
        Publish.house_inspector_id == id, Publish.house_type == 0).all()
    total = len(r)
    PER_PAGE = 4
    page, per_page, offset = get_page_args(page_parameter="p", per_page_parameter="pp", pp=PER_PAGE)
    pagination = Pagination(
        p=page,
        pp=per_page,
        total=total,
        format_total=True,
        format_number=True,
        page_parameter="p",
        per_page_parameter="pp",
        css_framework="bootstrap4",
        show_single_page=True,
    )
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    houses = db.session.query(NewHouse).join(Publish, Publish.house_id == NewHouse.index).filter(
        Publish.house_inspector_id == id, Publish.house_type == 0).slice(start, end)

    r2 = db.session.query(SecondHouse).join(Publish, Publish.house_id == SecondHouse.index).filter(
        Publish.house_inspector_id == id, Publish.house_type == 1).all()
    total = len(r2)
    page2, per_page2, offset2 = get_page_args(page_parameter="p2", per_page_parameter="pp2", pp2=PER_PAGE)
    pagination2 = Pagination(
        p2=page2,
        pp2=per_page2,
        total=total,
        format_total=True,
        format_number=True,
        page_parameter="p2",
        per_page_parameter="pp2",
        css_framework="bootstrap4",
        show_single_page=True,
    )
    start2 = (page2 - 1) * PER_PAGE
    end2 = start2 + PER_PAGE
    houses2 = db.session.query(SecondHouse).join(Publish, Publish.house_id == SecondHouse.index).filter(
        Publish.house_inspector_id == id, Publish.house_type == 1).slice(start2, end2)

    return render_template('house_inspector_item.html', contact_form=contact_form, login_status=login_status,
                           inspector_name=inspector_name, inspector_phone=inspector_phone,
                           inspector_email=inspector_email, inspector_img=inspector_img,
                           pagination=pagination, houses=houses,
                           pagination2=pagination2, houses2=houses2, session_role=session_role)


# 售房新闻单栏展示  --> 孙一鸣
@app.route('/house_info_item/<id>', methods=['GET', 'POST'])
def house_info_item(id):
    login_status = check_login_status()
    session_role = get_session_role()
    item = newsContent_dict[id]
    content = item['content']
    title = item['title']
    time = item['time']
    random_num = "../static/front_end/img/blog/0" + str(random.randint(1, 7)) + ".jpg"
    return render_template('house_info_item.html', content=content, title=title, time=time, session_role=session_role,
                           random_num=random_num, login_status=login_status, house_info_list=session['result_list'])


# 房屋新闻展示 --> 孙一鸣
@app.route('/house_info_list', methods=['GET', 'POST'])
def house_info_list():
    login_status = check_login_status()
    session_role = get_session_role()
    # 随机推荐
    q = Query('./estateApp/ir/index')
    res = q.standard_search('北京')
    # 存入缓存
    for item in res:
        if item['id'] not in newsContent_dict.keys():
            newsContent_dict[item['id']] = item
    result_list = []
    res = random.choices(res, k=6)
    # 存储返回前端数据
    for item in res:
        num = random.randint(1, 7)
        it = []
        url = "../static/front_end/img/blog/0" + str(num) + ".jpg"
        it.append(url)
        # it.append(item)
        it.append(item['id'])
        it.append(item['title'])
        it.append(item['time'])
        result_list.append(it)
    # 添加session为展示侧边栏使用
    if (len(result_list) >= 3):
        session['result_list'] = result_list[:3]
    else:
        session['result_list'] = result_list

    if request.method == "POST":
        # 获取搜索信息
        query = request.form.get('query')
        return redirect(url_for('news_ir', query=query))
    return render_template('house_info_list.html',
                           title_content='The Latest News of Houses', subtitle='Houses News',
                           html='house_info_list', login_status=login_status, session_role=session_role,
                           house_info_list=result_list)


# 新闻搜索引擎 --> 孙一鸣
@app.route('/news_ir/<string:query>', methods=['GET', 'POST'])
def news_ir(query):
    login_status = check_login_status()
    session_role = get_session_role()
    if request.method == "POST":
        # 获取搜索信息
        query = request.form.get('query')
        return redirect(url_for('news_ir', query=query))
    q = Query('./estateApp/ir/index')
    # 获取搜索结果
    res = q.standard_search(query)
    list_length = len(res)
    result_list = []
    # 存入缓存
    for item in res:
        if item['id'] not in newsContent_dict.keys():
            newsContent_dict[item['id']] = item
    for item in res:
        num = random.randint(1, 7)
        it = []
        url = "../static/front_end/img/blog/0" + str(num) + ".jpg"
        it.append(url)
        # it.append(item)
        it.append(item['id'])
        it.append(item['title'])
        it.append(item['time'])
        result_list.append(it)
    # 添加session为展示侧边栏使用
    if (len(result_list) >= 3):
        session['result_list'] = result_list[:3]
    else:
        session['result_list'] = result_list

    return render_template('house_info_list.html', title_content='The Latest News of Houses', subtitle='Houses News',
                           house_info_list=result_list, html='news_ir', list_length=list_length,
                           login_status=login_status, session_role=session_role)


# 个人主页
@app.route('/personal_page', methods=['GET', 'POST'])
def personal_page():
    login_status = check_login_status()
    session_role = get_session_role()
    if session.get('user_id') is None:
        return redirect(url_for('index'))
    user_id = session.get('user_id')
    user_in_db = User.query.filter(User.id == user_id).first()
    avatar_hash = hashlib.md5(user_in_db.emails.lower().encode('utf-8')).hexdigest()
    personal_img_url = avatars.gravatar(avatar_hash, size=150, default="identicon")

    name = user_in_db.name
    phone = user_in_db.phone
    email = user_in_db.emails
    all_appointment = []
    all_message = []
    appointment_in_db = Appointment.query.filter(Appointment.customer_user_id == user_id).all()
    message_in_db = Message.query.filter(Message.customer_user_id == user_id).all()
    today = datetime.datetime.today()
    format_pattern = '%Y-%m-%d'
    today_format = today.strftime(format_pattern)

    for each_appointment in appointment_in_db:
        appointment_day = str(each_appointment.appointment_year) + '-' + str(each_appointment.appointment_month) + \
                          '-' + str(each_appointment.appointment_date)
        if datetime.datetime.strptime(appointment_day, format_pattern) >= datetime.datetime.strptime(today_format,
                                                                                                     format_pattern):
            if each_appointment.house_type == 0:
                appointment_house = NewHouse.query.filter(NewHouse.index == each_appointment.house_id).first()
                house_type = 'New'
            else:
                appointment_house = SecondHouse.query.filter(SecondHouse.index == each_appointment.house_id).first()
                house_type = 'Second'
            house_name = appointment_house.house_name
            all_appointment.append({
                'appointment_date': str(each_appointment.appointment_year) + ' / ' +
                                    str(each_appointment.appointment_month) + ' / ' +
                                    str(each_appointment.appointment_date),
                'appointment_house': str(house_name),
                'appointment_content': str(each_appointment.content),
                'house_index': house_type + str(each_appointment.house_id)
            })

    for each_message in message_in_db:
        house_inspector_in_db = User.query.filter(User.id == each_message.house_inspector_user_id).first()
        house_inspector_name = house_inspector_in_db.name
        if each_message.status == 1:
            all_message.append({
                'message_content': each_message.content,
                'message_year': each_message.message_year,
                'message_month': each_message.message_month,
                'message_date': each_message.message_date,
                'house_inspector_name': house_inspector_name,
                'replied_year': each_message.replied_year,
                'replied_month': each_message.replied_month,
                'replied_date': each_message.replied_date,
                'replied_content': each_message.replied_content,
            })
        else:
            all_message.append({
                'message_content': each_message.content,
                'message_year': each_message.message_year,
                'message_month': each_message.message_month,
                'message_date': each_message.message_date,
                'house_inspector_name': house_inspector_name,
                'replied_year': '-',
                'replied_month': '-',
                'replied_date': '-',
                'replied_content': 'NOT REPLY YET',
            })
    return render_template('personal_page.html', login_status=login_status, personal_img_url=personal_img_url,
                           name=name, user_id=user_id, token=generate_token(user_in_db.password, expire=3600),
                           phone=phone, email=email, all_appointment=all_appointment, all_message=all_message,
                           session_role=session_role)


# 开发者页面
@app.route('/developer', methods=['GET', 'POST'])
def developer():
    login_status = check_login_status()
    session_role = get_session_role()
    return render_template('developer.html', login_status=login_status, session_role=session_role)


# 员工个人主页
@app.route('/personal_page_staff', methods=['GET', 'POST'])
def personal_page_staff():
    global new_house_number
    global second_hand_house_number
    global publish_index
    login_status = check_login_status()
    if login_status:
        user_id = session.get('user_id')
        user_in_db = User.query.filter(User.id == user_id).first()
        user_name = user_in_db.name
        user_email = user_in_db.emails
        avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
        user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")
    else:
        return redirect(url_for('login'))
    publish_new_house_form = PublishNewHouseForm()
    publish_second_hand_house_form = PublishSecondHandHouseForm()
    today = datetime.date.today()

    today_appointment = Appointment.query.filter(Appointment.appointment_year == int(str(today)[0:4]),
                                                 Appointment.appointment_month == int(str(today)[5:7]),
                                                 Appointment.appointment_date == int(str(today)[8:10]),
                                                 Appointment.house_inspector_user_id == int(session['user_id'])).all()
    today_appointment_number = len(today_appointment)

    total_appointment = db.session.query(Appointment).join(User, User.id == Appointment.customer_user_id).filter(
        Appointment.house_inspector_user_id == int(session['user_id']), User.role == 0).all()
    total_appointment_number = len(total_appointment)

    unread_message = db.session.query(Message).join(User, User.id == Message.customer_user_id).filter(
        Message.house_inspector_user_id == int(session['user_id']), User.role == 0, Message.status == 0).all()
    unread_message_number = len(unread_message)

    total_publish = Publish.query.filter(Publish.house_inspector_id == int(session['user_id'])).all()
    published_house_number = len(total_publish)
    # 上传新的房屋数据
    if publish_new_house_form.new_house_publish_submit.data:
        house_name = publish_new_house_form.house_name.data
        room = publish_new_house_form.room.data
        size = publish_new_house_form.size.data
        province = publish_new_house_form.province.data
        city = publish_new_house_form.city.data
        district = publish_new_house_form.district.data
        position = publish_new_house_form.position.data
        price_each_square_meter = publish_new_house_form.price_each_square_meter.data
        new_house_index = new_house_number + 1
        start_end_hour = publish_new_house_form.start_end_hour.data

        # # 判断地址是否为中文
        # flag = True
        # for i in range(len(position)):
        #     if (ord(position[i]) <= 122 and ord(position[i]) >= 41):  # 如果是汉字，则字符串长度加2
        #         flag = False
        #         break
        # if flag is False:
        #     flash("please enter the Chinese address!")
        if verify_new_house_input(house_name, room, size, province, city, district, price_each_square_meter, start_end_hour, position) == 0:
            room_description = str(room) + 'room'
            size_description = str(size) + 'MeterSquare'

            addr = esq([position])
            longtitude = addr[0][0]
            latitude = addr[0][1]

            # 更新 new house
            new_house_to_stored = NewHouse(
                index=new_house_index,
                province=pinyin(province),
                city=pinyin(city),
                house_name=pinyin(house_name),
                room=room_description,
                size=size_description,
                position=pinyin(position),
                district=pinyin(district),
                price_each_square_meter=price_each_square_meter,
                latitude=latitude,
                longtitude=longtitude
            )
            db.session.add(new_house_to_stored)
            db.session.commit()
            new_house_number = new_house_number + 1

            # 更新 publish
            available_time = str(publish_new_house_form.available_weekday.data) + '-' + str(start_end_hour)
            new_publish_index = publish_index + 1
            publish_to_stored = Publish(
                index=new_publish_index,
                house_type=0,
                house_id=new_house_index,
                house_inspector_id=user_id,
                available_time=available_time
            )
            db.session.add(publish_to_stored)
            db.session.commit()
            publish_index = publish_index + 1
            return redirect(url_for('house_info_staff'))
        else:
            print('Error')
            flash('Error Input, Please Check Again')

    if publish_second_hand_house_form.second_hand_house_publish_submit.data:
        second_hand_house_index = second_hand_house_number + 1
        province = publish_second_hand_house_form.province.data
        city = publish_second_hand_house_form.city.data
        house_name = publish_second_hand_house_form.house_name.data
        position = publish_second_hand_house_form.position.data
        price_each_square_meter = publish_second_hand_house_form.price_each_square_meter.data
        size = publish_second_hand_house_form.size.data
        start_end_hour = publish_second_hand_house_form.start_end_hour.data

        if verify_second_hand_house_input(house_name, size, province, city, price_each_square_meter, start_end_hour,
                                          position) == 0:
            addr = esq([position])
            longtitude = addr[0][0]
            latitude = addr[0][1]

            # 更新 second hand house
            second_hand_house_to_stored = SecondHouse(
                index=second_hand_house_index,
                province=pinyin(province),
                city=pinyin(city),
                house_name=pinyin(house_name),
                position=position,
                total_price=str(int(price_each_square_meter) * int(size)),
                price_each_square_meter=price_each_square_meter,
                size=size,
                latitude=latitude,
                longtitude=longtitude
            )
            db.session.add(second_hand_house_to_stored)
            db.session.commit()
            second_hand_house_number = second_hand_house_number + 1

            # 更新 publish
            available_time = str(publish_second_hand_house_form.available_weekday.data) + '-' + \
                             str(start_end_hour)
            new_publish_index = publish_index + 1
            publish_to_stored = Publish(
                index=new_publish_index,
                house_type=1,
                house_id=second_hand_house_index,
                house_inspector_id=user_id,
                available_time=available_time
            )
            db.session.add(publish_to_stored)
            db.session.commit()
            publish_index = publish_index + 1
        else:
            flash('Error Input, Please Check Again')
    return render_template('personal_page_staff.html', login_status=login_status, user_name=user_name,
                           user_img=user_img,
                           publish_new_house_form=publish_new_house_form,
                           publish_second_hand_house_form=publish_second_hand_house_form,
                           total_appointment_number=total_appointment_number,
                           today_appointment_number=today_appointment_number,
                           unread_message_number=unread_message_number, published_house_number=published_house_number)


# 员工所收到的邮件列表 -> 于佳悦
@app.route('/mail_list', methods=['GET', 'POST'])
def mail_list():
    login_status = check_login_status()
    if login_status:
        user_id = session.get('user_id')
        user_in_db = User.query.filter(User.id == user_id).first()
        user_name = user_in_db.name
        user_email = user_in_db.emails
        avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
        user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")

        # customers = User.query.filter(User.role == 0).all()
        unread = "unread"
        read = "read"

        # today = datetime.date.today()
        # format_pattern = '%Y-%m-%d'
        # today_format = datetime.datetime.strptime(str(today), format_pattern)
        # s2 = datetime.datetime.strptime('2021-5-4', format_pattern)

        today = datetime.datetime.today()
        format_pattern = '%Y-%m-%d'
        today_format = today.strftime(format_pattern)

        # 分页
        r1 = db.session.query(Appointment, User).filter(User.id == Appointment.customer_user_id).filter(
            and_(Appointment.house_inspector_user_id == user_id, User.role == 0)
        ).all()

        newlist = []
        for index, value in enumerate(r1):
            if datetime.datetime.strptime(today_format, format_pattern) <= datetime.datetime.strptime(str(value[0]),
                                                                                                      format_pattern):
                newlist.append(r1[index])
        r2 = db.session.query(Message, User).filter(User.id == Message.customer_user_id).filter(
            Message.house_inspector_user_id == user_id, User.role == 0).all()

        total = max(len(newlist), len(r2))
        PER_PAGE = 8
        page, per_page, offset = get_page_args(page_parameter="p", per_page_parameter="pp", pp=PER_PAGE)
        pagination = Pagination(
            p=page,
            pp=per_page,
            total=total,
            format_total=True,
            format_number=True,
            page_parameter="p",
            per_page_parameter="pp",
            css_framework="bootstrap4",
            show_single_page=True,
        )
        start = (page - 1) * PER_PAGE
        end = start + PER_PAGE
        appointments = newlist[start:end]
        messages = db.session.query(Message, User).filter(User.id == Message.customer_user_id).filter(
            Message.house_inspector_user_id == user_id, User.role == 0).slice(start, end)
        # customers = User.query.filter(User.role == 0, or_(User.appointments != None, User.messages != None)).slice(
        #     start, end)
    else:
        return redirect(url_for('login'))
    return render_template('mail_list.html', login_status=login_status, pagination=pagination,
                           user_id=user_id,
                           unread=unread, read=read,
                           user_name=user_name,
                           user_img=user_img, appointments=appointments, messages=messages)


# 员工查看邮件详情 & 回复邮件 -> 倪莎
@app.route('/mail_item/<type>/<id>', methods=['GET', 'POST'])
def mail_item(type, id):
    login_status = check_login_status()
    if login_status == False:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    user_in_db = User.query.filter(User.id == user_id).first()
    user_name = user_in_db.name
    user_email = user_in_db.emails
    avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")

    # 展示mail信息
    # message details
    if type == 'message':
        mail = Message.query.get(id)
        customer = User.query.filter(User.id == mail.customer_user_id).first()
        mail_item_display_message = {'id': id, 'buyer_name': customer.name,
                                     'message_date': mail.message_date, 'message_month': mail.message_month,
                                     'message_year': mail.message_year,
                                     'buyer_phone': customer.phone, 'buyer_email': customer.emails,
                                     'content': mail.content, 'status': mail.status}
        if mail.status == 0:
            # 回复mail-message
            reply_form = ReplyForm()
            if reply_form.validate_on_submit():
                today = datetime.date.today()
                mail.replied_content = reply_form.reply.data
                mail.replied_year = int(str(today)[0:4])
                mail.replied_month = int(str(today)[5:7])
                mail.replied_date = int(str(today)[8:10])
                mail.status = 1
                db.session.commit()
                return redirect(url_for('mail_list'))
            return render_template('mail_item.html', mail_item_display_message=mail_item_display_message,
                                   reply_form=reply_form, user_name=user_name, user_img=user_img)
        else:
            # 展示mail-message
            mail_item_display_message.update({'replied_date': mail.replied_date, 'replied_month': mail.replied_month,
                                              'replied_year': mail.replied_year,
                                              'replied_content': mail.replied_content})
            return render_template('mail_item.html', mail_item_display_message=mail_item_display_message,
                                   user_name=user_name, user_img=user_img)

    # appointment details
    elif type == 'appointment':
        mail = Appointment.query.filter(Appointment.id == id).first()
        customer = User.query.filter(User.id == mail.customer_user_id).first()
        mail_item_display_appointment = {'id': id, 'buyer_name': customer.name,
                                         'appointment_date': mail.appointment_date,
                                         'appointment_month': mail.appointment_month,
                                         'appointment_year': mail.appointment_year,
                                         'buyer_phone': customer.phone, 'buyer_email': customer.emails,
                                         'content': mail.content, 'status': mail.status}
        if mail.house_type == 0:
            house = NewHouse.query.filter(NewHouse.index == mail.house_id).first()
            house_type = 'New'
        else:
            house = SecondHouse.query.filter(SecondHouse.index == mail.house_id).first()
            house_type = 'Second'
        mail_item_display_appointment.update({'house_name': house.house_name, 'house_province': house.province,
                                              'house_city': house.city, 'house_position': house.position,
                                              'house_index': mail.house_id, 'house_type': house_type,
                                              'house_price': house.price_each_square_meter})
        # 更新appointment状态
        if mail.status == 0:
            read_form = AppointmentReadForm()
            if read_form.validate_on_submit():
                mail.status = 1
                db.session.commit()
                return redirect(url_for('mail_list'))
            return render_template('mail_item.html', mail_item_display_appointment=mail_item_display_appointment,
                                   read_form=read_form, user_name=user_name, user_img=user_img)
        else:
            unread_form = AppointmentUnReadForm()
            if unread_form.validate_on_submit():
                mail.status = 0
                db.session.commit()
                return redirect(url_for('mail_list'))
            return render_template('mail_item.html', mail_item_display_appointment=mail_item_display_appointment,
                                   unread_form=unread_form, user_name=user_name, user_img=user_img)

    return render_template('mail_item.html', user_name=user_name, user_img=user_img)


# 员工房间信息管理
@app.route('/house_info_staff', methods=['GET', 'POST'])
def house_info_staff():
    login_status = check_login_status()
    if login_status == False:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    user_in_db = User.query.filter(User.id == user_id).first()
    user_name = user_in_db.name
    user_email = user_in_db.emails
    avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")

    all_publish_in_db = Publish.query.filter(Publish.house_inspector_id == user_id).all()
    related_house = []
    for each_publish_in_db in all_publish_in_db:
        if int(each_publish_in_db.house_type) == 0:
            house_in_db = NewHouse.query.filter(NewHouse.index == each_publish_in_db.house_id).first()
            available_weekday, available_start_hour, available_end_hour = get_available_time(
                each_publish_in_db.available_time)
            related_house.append({
                'type': 0,
                'id': each_publish_in_db.index,
                'province': house_in_db.province,
                'city': house_in_db.city,
                'house_name': house_in_db.house_name,
                'available_weekday': available_weekday,
                'available_start_hour': available_start_hour,
                'available_end_hour': available_end_hour,
            })
        else:
            house_in_db = SecondHouse.query.filter(SecondHouse.index == each_publish_in_db.house_id).first()
            available_weekday, available_start_hour, available_end_hour = get_available_time(
                each_publish_in_db.available_time)
            related_house.append({
                'type': 1,
                'id': each_publish_in_db.index,
                'province': house_in_db.province,
                'city': house_in_db.city,
                'house_name': house_in_db.house_name,
                'available_weekday': available_weekday,
                'available_start_hour': available_start_hour,
                'available_end_hour': available_end_hour,
            })
    pagination_publish_house = generate_publish_house_pagination(len(related_house), 20, 'houses you published')
    return render_template('house_info_staff.html', related_house=related_house, user_name=user_name, user_img=user_img,
                           pagination=pagination_publish_house)


# 员工房间信息管理：具体的某一间房间的信息以及修改
@app.route('/house_info_item_staff/<type>/<id>', methods=['GET', 'POST'])
def house_info_item_staff(type, id):
    login_status = check_login_status()
    if login_status == False:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    modify_form = ModifyHouseInfoForm()
    user_in_db = User.query.filter(User.id == user_id).first()
    user_name = user_in_db.name
    user_email = user_in_db.emails
    avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")

    publish_in_db = Publish.query.filter(Publish.index == id).first()
    available_weekday, available_start_hour, available_end_hour = get_available_time(publish_in_db.available_time)
    house_info = {
        'available_weekday': available_weekday,
        'available_start_hour': available_start_hour,
        'available_end_hour': available_end_hour,
    }
    if int(type) == 0:
        new_house_in_db = NewHouse.query.filter(NewHouse.index == publish_in_db.house_id).first()
        house_info['type'] = 0
        house_info['province'] = new_house_in_db.province
        house_info['city'] = new_house_in_db.city
        house_info['house_name'] = new_house_in_db.house_name
        house_info['room'] = new_house_in_db.room
        house_info['size'] = new_house_in_db.size
        house_info['position'] = new_house_in_db.position
        house_info['district'] = new_house_in_db.district
        house_info['price_each_square_meter'] = new_house_in_db.price_each_square_meter
    else:
        second_hand_house_in_db = SecondHouse.query.filter(SecondHouse.index == publish_in_db.house_id).first()
        house_info['type'] = 1
        house_info['province'] = second_hand_house_in_db.province
        house_info['city'] = second_hand_house_in_db.city
        house_info['house_name'] = second_hand_house_in_db.house_name
        house_info['position'] = second_hand_house_in_db.position
        house_info['total_price'] = second_hand_house_in_db.total_price
        house_info['price_each_square_meter'] = second_hand_house_in_db.price_each_square_meter
        house_info['size'] = second_hand_house_in_db.size
    if modify_form.modify_submit.data:
        price_each_square_meter = modify_form.price_each_square_meter.data
        available_weekday = modify_form.available_weekday.data
        start_end_hour = modify_form.start_end_hour.data
        if verify_modify_house_info(price_each_square_meter, start_end_hour) == 0:
            if int(type) == 0:
                new_house_in_db = NewHouse.query.filter(NewHouse.index == publish_in_db.house_id).first()
                new_house_in_db.price_each_square_meter = price_each_square_meter
            else:
                second_hand_house_in_db = SecondHouse.query.filter(SecondHouse.index == publish_in_db.house_id).first()
                second_hand_house_in_db.price_each_square_meter = price_each_square_meter
            publish_in_db.available_time = str(available_weekday) + '-' + start_end_hour
            db.session.commit()
            return redirect(url_for('house_info_staff'))
        else:
            flash('Error Input, Please Check')
    return render_template('house_info_item_staff.html', house_info=house_info, user_name=user_name, user_img=user_img,
                           modify_form=modify_form)


# 用户展示页面
@app.route('/customers', methods=['GET', 'POST'])
def customers():
    login_status = check_login_status()
    if login_status == False:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    user_in_db = User.query.filter(User.id == user_id).first()
    user_name = user_in_db.name
    user_email = user_in_db.emails
    avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")

    # 分页
    r = User.query.filter(User.role == 0).all()
    total = len(r)
    PER_PAGE = 6
    page, per_page, offset = get_page_args(page_parameter="p", per_page_parameter="pp", pp=PER_PAGE)
    pagination = Pagination(
        p=page,
        pp=per_page,
        total=total,
        format_total=True,
        format_number=True,
        page_parameter="p",
        per_page_parameter="pp",
        css_framework="bootstrap4",
        show_single_page=True,
    )
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    customers = User.query.filter(User.role == 0).slice(start, end)

    avatar_hash = []
    for c in r:
        avatar_hash.append(hashlib.md5(c.emails.lower().encode('utf-8')).hexdigest())
    return render_template('customers.html', customers=customers, avatar_hash=avatar_hash, user_name=user_name,
                           user_img=user_img, pagination=pagination)


# 房价预测
@app.route('/show_predict/<output>/<query>', methods=['GET', 'POST'])
def show_predict(output, query):
    login_status = check_login_status()
    if login_status == False:
        return redirect(url_for('login'))
    user_id = session.get('user_id')
    user_in_db = User.query.filter(User.id == user_id).first()
    user_name = user_in_db.name
    user_email = user_in_db.emails
    avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")

    if request.method == "POST":
        query = request.values.get("query")
        address = request.values.get("address")
        room = request.values.get("room_num")
        size = request.values.get("size")
        session['predict_msg'] = [query, address, size, room]
        # 获取经纬度
        addr = esq([address])
        longtitude = addr[0][0]
        latitude = addr[0][1]

        if query == 'new house':
            model = pickle.load(open('./estateApp/new_house_model.pkl', 'rb'))
            float_features = []
            float_features.append(int(room))
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longtitude)
            type = 1

        elif query == 'second-hand house':
            model = pickle.load(open('./estateApp/second_hand_house_model.pkl', 'rb'))
            float_features = []
            float_features.append(int(size))
            float_features.append(latitude)
            float_features.append(longtitude)
            type = 2
        final_features = [np.array(float_features)]
        prediction = model.predict(final_features)
        output = round(prediction[0], 2)  # 保留小数点后两位

        return redirect(url_for('show_predict', output=output, query=type))

    output = float(output)
    if query == '1':
        prediction_scope = 'The range is between ¥ {}/㎡ to ¥ {}/㎡'.format(output - 1140, output + 1053)
    else:
        prediction_scope = 'The range is between ¥ {}/㎡ to ¥ {}/㎡'.format(output - 585, output + 550)

    return render_template('price_predict.html', output=output, prediction_scope=prediction_scope, user_name=user_name,
                           user_img=user_img, message=session['predict_msg'])


# XAI预测图
@app.route('/xai_ajax', methods=['GET', 'POST'])
def xai_ajax():
    query = request.values.get('query')
    address = request.values.get('address')
    room = request.values.get('room_num')
    size = request.values.get('size')
    room_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    size_list = [30, 60, 90, 120, 150, 180, 210, 240, 270, 300]
    # 获取经纬度
    addr = esq([address])
    longitude = addr[0][0]  # 经度
    latitude = addr[0][1]  # 纬度

    output_list_room = []
    output_list_size = []

    # 新房才有房间数：
    if query == 'new house':
        for r in room_list:
            # 新房
            if query == 'new house':
                output, low, high, accuracy = price_model_predict("0", longitude, latitude, r, size)
            # 二手房
            elif query == 'second-hand house':
                output, low, high, accuracy = price_model_predict("1", longitude, latitude, r, size)

            output_list_room.append(output)

    for s in size_list:
        # 新房
        if query == 'new house':
            output, low, high, accuracy = price_model_predict("0", longitude, latitude, room, s)
        # 二手房
        elif query == 'second-hand house':
            output, low, high, accuracy = price_model_predict("1", longitude, latitude, room, s)

        output_list_size.append(output)

    if query == 'new house':
        result_dict = {
            "output_list_size": output_list_size,
            "output_list_room": output_list_room
        }
    else:
        result_dict = {
            "output_list_size": output_list_size
        }
    return jsonify(result_dict)


# 房价页面预测
@app.route('/price_ajax', methods=['GET', 'POST'])
def price_ajax():
    query = request.values.get('query')
    address = request.values.get('address')
    room = request.values.get('room_num')
    size = request.values.get('size')

    # 获取经纬度
    addr = esq([address])
    longitude = addr[0][0]  # 经度
    latitude = addr[0][1]  # 纬度

    # 新房
    if query == 'new house':
        print(room + "-----")
        output, low, high, accuracy = price_model_predict("0", longitude, latitude, room, size)

    elif query == 'second-hand house':
        output, low, high, accuracy = price_model_predict("1", longitude, latitude, room, size)

    area = [low, high, accuracy]
    swap = session["price_list"]
    swap.append(output)
    session["price_list"] = swap
    ajax_result = {
        "line_graph": session["price_list"],
        "area": area
    }
    return jsonify(ajax_result)


# 房价预测
@app.route('/price_predict', methods=['GET', 'POST'])
def price_predict():
    login_status = check_login_status()
    if login_status == False:
        return redirect(url_for('login'))
    session["price_list"] = []
    user_id = session.get('user_id')
    user_in_db = User.query.filter(User.id == user_id).first()
    user_name = user_in_db.name
    user_email = user_in_db.emails
    avatar_hash = hashlib.md5(user_email.lower().encode('utf-8')).hexdigest()
    user_img = avatars.gravatar(avatar_hash, size=50, default="wavatar")

    # return redirect(url_for('price_predict', output=output))

    return render_template('price_predict.html', user_name=user_name, user_img=user_img)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if session.get('user_id') is not None:
        user_id = session.get('user_id')
    session.clear()
    return redirect(url_for('index'))


# 过滤器分类
def house_filter(filter):
    up = 99999
    down = 0
    if filter == 1:
        up = 5000
        down = 0
    elif filter == 2:
        up = 7500
        down = 5000
    elif filter == 3:
        up = 10000
        down = 7500
    elif filter == 4:
        up = 12500
        down = 10000
    elif filter == 5:
        up = 15000
        down = 12500
    elif filter == 6:
        up = 99999
        down = 15000
    return up, down


# search_result 生成房产搜索结果:
# para. - query:房产类型, search_query:搜索关键词, filter:房价区间
# return - list[ dict{:} ]
def generate_search_result_list(query, search_query, filter):
    session["search_query"] = search_query
    result_house_list = []
    up, down = house_filter(int(filter))
    if search_query == None:
        search_query = ''
        session["search_query"] = search_query
    if query == '1':
        # 获得中包含关键词的新房
        # 1. 数据库直接查询

        result_house_list_temp = NewHouse.query.filter(or_
                                                       (NewHouse.province.contains(search_query),
                                                        NewHouse.city.contains(search_query),
                                                        NewHouse.house_name.contains(search_query),
                                                        NewHouse.position.contains(search_query),
                                                        NewHouse.district.contains(search_query)
                                                        )).all()
        # result_house_list_temp = new_house_by_filter(filter)
        # 2.如果信息检索没有查出，再使用index检索
        if len(result_house_list_temp) == 0:
            # 使用信息检索查询
            q = QueryNew('./estateApp/ir/index_new')
            # 获取搜索结果
            result_house_list_temp = q.standard_search(search_query)

        # 3.如果直接查询和信息检索都没有，则使用模糊查询
        if len(result_house_list_temp) == 0:
            result_house_list_temp = NewHouse.query.filter(or_
                                                           (NewHouse.province.like(search_query[:1].upper() + '%'),
                                                            NewHouse.city.like(search_query[:1].upper() + '%')
                                                            )).all()
            # result_house_list_temp = new_house_by_filter_vague(filter)
        # 生成macro字典
        for nh in result_house_list_temp:
            # id, image_url, house_name, address, price, user_id, house_inspector_name
            if str(type(nh)) != '<class \'estateApp.models.NewHouse\'>':
                if int(nh['price_each_square_meter']) < down or int(nh['price_each_square_meter']) > up:
                    continue
                nh_id = 'New' + str(nh['index'])
                img_num = str(int(nh['index']) % 210)
                image_url = 'image/' + img_num + '.jpg'
                house_name = str(nh['house_name_pinyin'])
                address = nh['position_pinyin']
                price = nh['price_each_square_meter']
                cls = category_price(float(price))
                user_id = 1
                house_inspector_name = nh['city_pinyin']
            else:
                if int(nh.price_each_square_meter) < down or int(nh.price_each_square_meter) > up:
                    continue
                nh_id = 'New' + str(nh.index)
                img_num = str(int(nh.index) % 210)
                image_url = 'image/' + img_num + '.jpg'
                house_name = str(nh.house_name)
                address = nh.position
                price = nh.price_each_square_meter
                cls = category_price(float(price))
                user_id = 1
                house_inspector_name = nh.city
            result_house_item_temp = {'id': nh_id, 'image_url': image_url, 'house_name': house_name,
                                      'address': address, 'price': price, 'user_id': user_id,
                                      'house_inspector_name': house_inspector_name, 'class': cls}
            result_house_list.append(result_house_item_temp)
    else:
        # 获得中包含关键词的二手房
        # 1. 数据库直接查询
        result_house_list_temp = SecondHouse.query.filter(or_
                                                          (SecondHouse.province.contains(search_query),
                                                           SecondHouse.city.contains(search_query),
                                                           SecondHouse.house_name.contains(search_query),
                                                           SecondHouse.position.contains(search_query),
                                                           )).all()
        # result_house_list_temp = second_house_by_filter(filter)

        # 2.如果信息检索没有查出，再使用index检索
        if len(result_house_list_temp) == 0:
            # 使用信息检索查询
            q = QuerySecond('./estateApp/ir/index_second')
            # 获取搜索结果
            result_house_list_temp = q.standard_search(search_query)

        # 3.如果直接查询和信息检索都没有，则使用模糊查询
        if len(result_house_list_temp) == 0:
            result_house_list_temp = SecondHouse.query.filter(or_
                (SecondHouse.province.like(
                search_query[:1].upper() + '%'),
                SecondHouse.city.like(search_query[:1].upper() + '%')
            )).all()
            # result_house_list_temp = second_house_by_filter_vague(filter)

        # 生成marco字典
        for shh in result_house_list_temp:
            if str(type(shh)) != '<class \'estateApp.models.SecondHouse\'>':
                if int(shh['price_each_square_meter']) < down or int(shh['price_each_square_meter']) > up:
                    continue
                shh_id = 'Second' + str(shh['index'])
                img_num = str(int(shh['index']) % 210)
                image_url = 'image/' + img_num + '.jpg'
                house_name = str(shh['house_name_pinyin'])
                address = shh['position_pinyin']
                price = shh['price_each_square_meter']
                cls = category_price(float(price))
                user_id = 1
                house_inspector_name = shh['city_pinyin']
            else:
                if int(shh.price_each_square_meter) < down or int(shh.price_each_square_meter) > up:
                    continue
                # id, image_url, house_name, address, price, user_id, house_inspector_name
                shh_id = 'Second' + str(shh.index)
                img_num = str(int(shh.index) % 210)
                image_url = 'image/' + img_num + '.jpg'
                house_name = str(shh.house_name)
                address = shh.position
                price = shh.price_each_square_meter
                cls = category_price(float(price))
                user_id = 1
                house_inspector_name = shh.city
            result_house_item_temp = {'id': shh_id, 'image_url': image_url, 'house_name': house_name,
                                      'address': address, 'price': price, 'user_id': user_id,
                                      'house_inspector_name': house_inspector_name, 'class': cls}
            result_house_list.append(result_house_item_temp)
    if session.get('user_id') is not None:
        user_id = session.get('user_id')
        for i in range(len(result_house_list)):
            each_house_item = result_house_list[i]
            if 'Second' in str(each_house_item['id']):
                house_type = 1
            else:
                house_type = 0
            house_id = re.findall(r"\d+\.?\d*", each_house_item['id'])[0]
            rating = UserBasedHouseRecommendationSystem.check_rating_status(user_id=str(user_id),
                                                                            house_id=str(house_id),
                                                                            house_type=str(house_type))
            each_house_item['rating'] = rating
            result_house_list[i] = each_house_item
        result_house_list = sorted(result_house_list, key=lambda e: float(e.__getitem__('rating')), reverse=True)
    return result_house_list


# search_result 生成房产搜索结果分页:
# para. - result_house_list_length:房产搜索结果列表的长度，house_type：房子类型的名称
# return - paginate object
def generate_search_result_pagination(result_house_list_length, house_type):
    page, per_page, offset = get_page_args(page_parameter="p", per_page_parameter="pp", pp=12)
    display_search_message = '<i class="fal fa-ellipsis-h"></i> Displaying <b>{start} - {end}</b> results in total <b>{total}</b> ' + house_type + ' search results. <i class="fal fa-ellipsis-h"></i>'
    pagination = Pagination(
        p=page,
        pp=per_page,
        total=result_house_list_length,
        record_name="result_house_list",
        format_total=True,
        format_number=True,
        page_parameter="p",
        per_page_parameter="pp",
        css_framework="bootstrap4",
        show_single_page=True,
        prev_label='<i class="far fa-chevron-left"></i>',
        next_label='<i class="far fa-chevron-right"></i>',
        display_msg=display_search_message,
    )
    return pagination


# house_info_staff 生成结果分页:
def generate_publish_house_pagination(house_list_length, per_page_item_num, display_info):
    page, per_page, offset = get_page_args(page_parameter="p", per_page_parameter="pp", pp=per_page_item_num)
    display_search_message = 'Displaying <b>{start} - {end}</b> in total <b>{total}</b> ' + display_info + '.'
    pagination = Pagination(
        p=page,
        pp=per_page,
        total=house_list_length,
        record_name="result",
        format_total=True,
        format_number=True,
        page_parameter="p",
        per_page_parameter="pp",
        css_framework="bootstrap4",
        show_single_page=True,
        # prev_label='<i class="far fa-chevron-left"></i>',
        # next_label='<i class="far fa-chevron-right"></i>',
        display_msg=display_search_message,
    )
    return pagination


# 房价预测(api)
@app.route('/price_p', methods=['GET', 'POST'])
def price_p():
    if request.method == "POST":
        user_id = request.values.get('user_id')
        query = request.values.get("query")
        address = request.values.get("address")
        room = request.values.get("room_num")
        size = request.values.get("size")
        token = request.values.get("token")
        developer_in_db = User.query.filter(User.id == user_id).first()

        if certify_token(developer_in_db.password, token):
            # 获取经纬度
            addr = esq([address])
            longtitude = addr[0][0]
            latitude = addr[0][1]

            if query == '0':
                model = pickle.load(open('./estateApp/new_house_model.pkl', 'rb'))
                float_features = []
                float_features.append(int(room))
                float_features.append(int(size))
                float_features.append(latitude)
                float_features.append(longtitude)

            elif query == '1':
                model = pickle.load(open('./estateApp/second_hand_house_model.pkl', 'rb'))
                float_features = []
                float_features.append(int(size))
                float_features.append(latitude)
                float_features.append(longtitude)

            final_features = [np.array(float_features)]
            prediction = model.predict(final_features)
            output = round(prediction[0], 2)  # 保留小数点后两位
            feedback = {
                'longtitude': longtitude,
                'latitude': latitude,
                'predicted_house_price': output,
            }
            return json.dumps(feedback)
        else:
            feedback = {
                'error': 'token verification error'
            }
            return json.dumps(feedback)
    # return render_template('price_predict.html')


# rating:
@app.route('/score', methods=['GET', 'POST'])
def score():
    user_id = session.get('user_id')
    if user_id is not None:
        score = request.form.get('score')
        lists = score.split(',')  # 传过来的第一个值是house_type，第二个是house_id，第三个是分数
        UserBasedHouseRecommendationSystem.update(house_type=lists[0], house_id=str(lists[1]), user_id=str(user_id),
                                                  house_rating=lists[2])
        return jsonify(lists[2])


@app.route('/download_sdk/<filename>')
def download_sdk(filename):
    file_path = Config.SDK_DIR
    return send_from_directory(file_path, filename, as_attachment=True)


# 用于house inspector 在发布房源的时候获取房价的预测值
@app.route('/house_price_auto', methods=['POST'])
def house_price_auto():
    recv_data = request.get_data()
    if recv_data:
        recv_data = str(recv_data, encoding='utf-8')
        data_info = recv_data.split('&')
        parameter_list = []
        for each_data_info in data_info:
            parameter = each_data_info.split('=')[1]
            parameter_list.append(parameter)
        query, address, room, size = str(parameter_list[0]), str(parameter_list[1]), str(parameter_list[2]), str(
            parameter_list[3])
        print(query, address, room, size)
        return get_api_feedback(query, address, room, size)
