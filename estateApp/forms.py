from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, SubmitField, PasswordField, IntegerField, TextAreaField, RadioField, FloatField, \
    SelectField, DateField
from wtforms.validators import DataRequired, URL


class SearchHouseForm(FlaskForm):
    house_info = StringField('house_info', validators=[DataRequired()])
    submit = SubmitField('search')


class RegisterForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()], render_kw={"placeholder": "Input Your Name"})
    password = PasswordField('password', validators=[DataRequired()], render_kw={"placeholder": "Input Your Password"})
    phone = StringField('phone', validators=[DataRequired()], render_kw={"placeholder": "Input Your Phone"})
    email = StringField('email', validators=[DataRequired()], render_kw={"placeholder": "Input Your Email"})
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    name = StringField('name', validators=[DataRequired()], render_kw={"placeholder": "Input Your Name"})
    password = PasswordField('password', validators=[DataRequired()], render_kw={"placeholder": "Input Your Password"})
    submit = SubmitField('Login')


class ContactForm(FlaskForm):
    content = TextAreaField('', validators=[DataRequired()], render_kw={"placeholder": "Write Message"})
    submit = SubmitField('Send Message')


class ReplyForm(FlaskForm):
    reply = TextAreaField('', validators=[DataRequired()], render_kw={"placeholder": "Reply this customer here..."})
    submit = SubmitField('Send Message')


class AppointmentForm(FlaskForm):
    time = DateField(render_kw={"placeholder": "Book Date (yyyy-mm-dd)"}, format='%Y-%m-%d', validators=[DataRequired()])
    message = TextAreaField('', render_kw={"placeholder": "Write Message (optional)"})
    submit = SubmitField('Send Message')


class AppointmentReadForm(FlaskForm):
    submit = SubmitField('Mark as read')


class AppointmentUnReadForm(FlaskForm):
    submit = SubmitField('Unread')


class PublishNewHouseForm(FlaskForm):
    house_name = StringField('house_name', validators=[DataRequired()], render_kw={"placeholder": "Input House Name"})
    room = StringField('room', validators=[DataRequired()],
                       render_kw={"placeholder": "Input Room Number, eg:2"})
    size = StringField('size', validators=[DataRequired()], render_kw={"placeholder": "Input House Size, eg:100"})
    province = StringField('province', validators=[DataRequired()], render_kw={"placeholder": "Input Province"})
    city = StringField('city', validators=[DataRequired()], render_kw={"placeholder": "Input City"})
    district = StringField('district', validators=[DataRequired()], render_kw={"placeholder": "Input District"})
    position = StringField('position', validators=[DataRequired()], render_kw={"placeholder": "Input House Position eg: 北京市朝阳区北京工业大学"})
    price_each_square_meter = IntegerField('Price Each Square Meter', validators=[DataRequired()],
                                           render_kw={"placeholder": "Price Each Square Meter, eg: 1000"})
    available_weekday = SelectField('available weekday',
                                    choices=[('1', 'Monday'),  ('2', 'Tuesday'),
                                             ('3', 'Wednesday'),  ('4', 'Thursday'),
                                             ('5', 'Friday'),  ('6', 'Saturday'), ('7', 'Sunday')],
                                    validators=[DataRequired()])
    start_end_hour = StringField('start_end_hour', validators=[DataRequired()],
                                 render_kw={"placeholder": "Input start and end hour(Format: X-Y, eg:17-22)"})
    new_house_publish_submit = SubmitField('Publish New House')


class PublishSecondHandHouseForm(FlaskForm):
    house_name = StringField('house_name', validators=[DataRequired()], render_kw={"placeholder": "Input House Name"})
    room = StringField('room', validators=[DataRequired()],
                       render_kw={"placeholder": "Input Room Number"})
    size = StringField('size', validators=[DataRequired()], render_kw={"placeholder": "Input House Size"})
    province = StringField('province', validators=[DataRequired()], render_kw={"placeholder": "Input Province"})
    city = StringField('city', validators=[DataRequired()], render_kw={"placeholder": "Input City"})
    position = StringField('position', validators=[DataRequired()], render_kw={"placeholder": "Input House Position eg: 北京市朝阳区北京工业大学"})
    price_each_square_meter = IntegerField('Price Each Square Meter', validators=[DataRequired()],
                                           render_kw={"placeholder": "Price Each Square Meter, eg: 1000"})
    available_weekday = SelectField('available weekday',
                                    choices=[('1', 'Monday'), ('2', 'Tuesday'),
                                             ('3', 'Wednesday'), ('4', 'Thursday'),
                                             ('5', 'Friday'), ('6', 'Saturday'), ('7', 'Sunday')],
                                    validators=[DataRequired()])
    start_end_hour = StringField('start_end_hour', validators=[DataRequired()],
                                 render_kw={"placeholder": "Input start and end hour(Format: X-Y, eg:17-22)"})
    second_hand_house_publish_submit = SubmitField('Publish Second Hand House')


class ModifyHouseInfoForm(FlaskForm):
    price_each_square_meter = IntegerField('Price Each Square Meter', validators=[DataRequired()],
                                           render_kw={"placeholder": "Price Each Square Meter, eg:1000"})
    available_weekday = SelectField('available weekday',
                                    choices=[('1', 'Monday'), ('2', 'Tuesday'),
                                             ('3', 'Wednesday'), ('4', 'Thursday'),
                                             ('5', 'Friday'), ('6', 'Saturday'), ('7', 'Sunday')],
                                    validators=[DataRequired()])
    start_end_hour = StringField('start_end_hour', validators=[DataRequired()],
                                 render_kw={"placeholder": "Input start and end hour(Format: X-Y, eg:17-22)"})
    modify_submit = SubmitField('Modify House Info')



