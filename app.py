from flask import Flask, render_template, redirect, url_for, request, flash, session
#from data import Articles
from flaskext.mysql import MySQL
from wtforms import Form, StringField, PasswordField, TextAreaField, validators
from wtforms.fields.html5 import EmailField

import time
import datetime


mysql = MySQL()
app = Flask(__name__)

# Config MySQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'web_forum'
app.secret_key = 'super secret key'
mysql.init_app(app)


@app.route('/')
def index():
    if session.get('logged_in') is None:
        session['logged_in'] = False

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute('''select * from Post''')
    result = cur.fetchall()
    view_posts = [list(i) for i in result]
    # print(view_posts)
    if len(view_posts) is 0:
        flash('No posts to display')
    else:
        print('to check if itw working')
    return render_template('index.html', view_posts=view_posts)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.DataRequired(), validators.Length(min=1, max=50)])
    email = EmailField('Email', [validators.DataRequired(), validators.Length(min=6, max=50), validators.Email()])
    password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')

# Login Form Class


class LoginForm(Form):
    email = StringField('Email')
    password = PasswordField('Password')

# search class


class Post(Form):
    title = StringField('Post Title')
    desc = StringField('Decription')


# User Register


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        register_flag = 0

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("INSERT INTO user(username, emailid, password, phone, dob, gender) VALUES(%s, %s, %s, %s, %s, %s)", (name, email, password, "", "", 'M'))
        conn.commit()
        register_flag = 1
        cur.close()

        if register_flag == 1:
            flash('You have registered successfully')
            return redirect(url_for('login'))
    return render_template('register.html', title='Get Registered', form=form)

# User login


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if session.get('logged_in') is None:
        session['logged_in'] = False

    session['logged_in'] = False
    session['logged_user_id'] = ""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data
        flag = 0

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM user WHERE emailid = %s and password = %s", (email, password))

        for (emailid) in cur:
            print("{}".format(emailid))
            flag = 1
            user_id = emailid[0]

        cur.close()
        if flag == 0:
            flash('Incorrect username/password.')
        else:
            session['logged_in'] = True
            session['logged_user_id'] = form.email.data
            session['logged_user_id_num'] = user_id
            flash('You were successfully logged in')
            return redirect(url_for('view'))
    return render_template('login.html', title='Login', form=form)

@app.route('/my_posts', methods=['GET', 'POST'])
def my_posts():
    if session.get('logged_in') is None:
        session['logged_in'] = False

    if session['logged_in'] == True:
        conn = mysql.connect()
        cur = conn.cursor()
        
        cur.execute('''select * from post where user_id = (Select user_id from user where emailid = %s Limit 1)''', session['logged_user_id'])
        result = cur.fetchall()
        posts = [list(i) for i in result]
        
        
        return render_template('my_posts.html', title='My Posts', posts=posts)
    else:
        return render_template('index.html', title='Home')


@app.route('/edit_post', methods=['GET', 'POST'])
def edit_post():
    if session.get('logged_in') is None:
        session['logged_in'] = False

    if session['logged_in'] == True:
        if request.method == 'POST':
            post_id = request.form['post_id']
            print(post_id)
            conn = mysql.connect()
            cur = conn.cursor()
            cur.execute('''select * from post where post_id = %s''', post_id)
            result = cur.fetchone()
            post = result
            
        return render_template('edit_post.html', title='Edit Post', post=post)
    else:
        return render_template('index.html', title='Home')





@app.route('/view', methods=['GET', 'POST'])
def view():
    if session.get('logged_in') is None:
        session['logged_in'] = False

    if session['logged_in'] == True:
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute('''select * from Post''')
        result = cur.fetchall()
        view_posts = [list(i) for i in result]
        # print(view_posts)
        if len(view_posts) is 0:
            flash('No posts to display')
        else:
            print('to check if itw working')
        return render_template('view.html', view_posts=view_posts)
    else:
        return render_template('index.html', title='View Post')


@app.route('/post', methods=['GET', 'POST'])
def post():
    if session.get('logged_in') is None:
        session['logged_in'] = False

    if session['logged_in'] == True:
        conn = mysql.connect()
        cur = conn.cursor()
        if request.method == 'POST':
            post_id = request.form['id']
            c = request.form['comment']
            cur.execute("INSERT INTO comments(post_id, user_id, comment_text) VALUES(%s, %s, %s)", (post_id, session['logged_user_id_num'], c))
            conn.commit()
        else:
            post_id = request.args.get('id')

        cur.execute('select * from post where post_id = %s', post_id)
        post = cur.fetchone()
        cur.execute('select * from user where user_id = %s', post[1])
        user = cur.fetchone()

        cur.execute('select * from comments where post_id = %s', post_id)
        result = cur.fetchall()
        comments = [list(i) for i in result]
        # Not sure if we need to sort by date, so remove comment if we need to
        # comments = sorted(comments, key=lambda comment: comment[4])
        for i, c in enumerate(comments):
            cur.execute('select * from user where user_id = %s', c[2])
            commentUser = cur.fetchone()
            c.append(commentUser[1])
            comments[i] = c
        return render_template('post.html', post=post, comments=comments, user=(user[0], user[1]))
    else:
        return render_template('index.html', title='Post')

# Post Form Class


class CreatePostForm(Form):
    title = StringField('Title', [validators.DataRequired(), validators.Length(min=1, max=50)])
    body = TextAreaField('Body', [validators.DataRequired(), validators.Length(min=1, max=5000)])


@app.route('/createPost', methods=['GET', 'POST'])
def createPost():
    if session.get('logged_in') is None:
        session['logged_in'] = False

    if session['logged_in'] == True:
        form = CreatePostForm(request.form)
        if request.method == 'POST' and form.validate():

            timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            title = form.title.data
            body = form.body.data
            category = request.form["category"]
            user_email = session['logged_user_id']

            conn = mysql.connect()
            cur = conn.cursor()
            cur.execute("SELECT * FROM user WHERE emailid = %s", (user_email))
            for (user) in cur:
                user_id = str(user[0])
            conn = mysql.connect()
            cur = conn.cursor()
            cur.execute("INSERT INTO post(category_id, post_text, post_title, timestamp, user_id) VALUES(%s, %s, %s, %s, %s)", (category, body, title, timestamp, user_id))
            conn.commit()

            return render_template('post.html')

        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM category")
        categories = []
        for (category) in cur:
            categories.append(category)
        cur.close()

        return render_template('createPost.html', categories=categories, form=form)
    else:
        return render_template('index.html', title='Create Post')


# new changes -- aneesh to work on this.


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == "POST":
        conn = mysql.connect()
        cur = conn.cursor()
        cur.execute('''select * from Post where post_title = %s''', request.form['search'])
        result = cur.fetchall()
        searched_posts = [list(i) for i in result]
        # print(searched_posts)
        if len(searched_posts) is 0:
            flash('No results Found!')
        else:
            print
            flash('Values Found!')
        return render_template('search.html', searched_posts=searched_posts)  # <- Here you jump away from whatever result you create
   # return render_template('view.html')


def getCategoryList():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM category")
    result = cur.fetchall()
    category_list = [list(i) for i in result]

    return category_list


if __name__ == '__main__':

    app.run(debug=True, host='127.0.0.1')
