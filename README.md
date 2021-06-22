Before you run this web application, please make sure that you have installed the following Python Library by running the command:
```shell
pip install Flask Flask-WTF WTForms Flask-SQLAlchemy
pip install gunicorn gevent
pip install python-dotenv wheel
pip install whoosh jieba
pip install numpy sklearn
pip install flask-avatars
pip install flask-paginate
pip install requests
pip install pypinyin
```

The whole project structure should be like that:

```markdown
estate
| - coverageReport
| - estateApp
| 		- ir
|	 	- ml
|		- rs
|		- sdk
|		- static
|			- back_end
|			- front_end
|		- templates
|   	- __init__.py
|   	- config.py
|   	- forms.py
|   	- models.py
|   	- routes.py
|   	- estate.db
| - flaskenv
| - .flaskenv
| - estate.py
| - gunicorn.py
| - README.md
```
if you can not create db file, please change the version as follow
``` shell
pip install Flask-SQLAlchemy==2.4.4
pip install SQLAlchemy==1.3.23
```
Especially, if the network request can not be executed properly (such as Position Query executed by GaoDe API), you should try the following:
```shell
pip install urllib3==1.25.8
```