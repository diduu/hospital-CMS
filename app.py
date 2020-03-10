
from medications import medicationsList, generateChart
from flask import Flask, url_for, redirect, render_template, request, session, abort, flash, Response, stream_with_context
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from functools import wraps
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db' #configuring database
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

engine = create_engine('sqlite:///data.db', echo = True)
meta = MetaData()


#Creates a table for login form with id, email and password
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)

#Creates a table for web page content with id and text
pageContent = Table(
    'content', meta,
    Column("page_id", Integer, primary_key=True),
    Column("content", Text),
)

#Creates a table to store announcements with id, title, date, description
class Announcement(db.Model):
    page_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(10000), nullable=False)
    date = db.Column(db.DateTime(), nullable=False)
    #image = db.Column(db.BLOB)

meta.create_all(engine)
db.create_all()


'''
class Page(Base):
    __tablename__ = 'content'
    Column("page_id", Integer, primary_key=True)
    Column("content", Text)
'''

#Populate content table with input from add new page content
@app.route("/populateContent", methods=['POST'])
def populateContent():
    inputString = request.form['editBox']
    #INSERT INTO content (content) VALUES (inputString)
    insertStatement = pageContent.insert().values(content = inputString)
    conn = engine.connect()
    result = conn.execute(insertStatement)
    return redirect(url_for('index'))

#Update content table with input from edit.html
@app.route("/updateContent", methods=['POST'])
def updateContent():
    inputString = request.form['editBox']
    #UPDATE first row in table content
    updateStatement = pageContent.update().where(pageContent.c.page_id==1).values(content = inputString)
    conn = engine.connect()
    result = conn.execute(updateStatement)
    return redirect(url_for('index'))


@app.route('/index')
#content table query for index.html
def retrieveContentIndex():
    # Equivalent to SELECT * FROM pageContent
    select = pageContent.select()
    conn = engine.connect()
    result = conn.execute(select)
    outputRow = result.fetchone()
    for row in result:
        if (row.page_id == 1):
            outputRow = row
    return render_template('index.html', content=outputRow.content)

@app.route('/edit')
#content table query for Edit.html
def retrieveContentEdit():
    # Equivalent to SELECT * FROM pageContent
    select = pageContent.select()
    conn = engine.connect()
    result = conn.execute(select)
    outputRow = result.fetchone()
    for row in result:
        if (row.page_id == 1):
            outputRow = row
    return render_template('edit.html', content=outputRow.content)




@app.route('/medication', methods=['GET', 'POST'])
def medication():
    if request.method == 'POST':
        selected = [med for med in medicationsList if med.name in request.form]
        return render_template('chart.html', chart=generateChart(selected))

    return render_template('medication.html', medications=medicationsList)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/login')
def login():
    return render_template('auth/login.html')


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash("You need to login first")
            return redirect(url_for('login'))

    return wrap

@app.route("/logmein", methods=['POST'])
def logmein():
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(email = username).first()

    if not user:
        flash('Invalid credentials')
        return redirect(url_for('login'))
    else:
        if user.password != password:
            flash('Invalid credentials')
            return redirect(url_for('login'))
        else:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))



@app.route("/logout")
@login_required
def logout():
    session['logged_in'] = False
    session.clear()
    return redirect(url_for('index'))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route("/edit")
@login_required
def edit():
    return render_template('edit.html')


@app.route("/users")
@login_required
def users():
    conn = engine.connect()
    query = "SELECT id, email from user"
    result = conn.execute(query)
    data = result.fetchall()
    return render_template('users.html', data = data)


@app.route("/addUser")
@login_required
def addUser():
    return render_template('addUser.html')

@app.route("/addContentUser", methods=['POST'])
def addContentUser():
    userEmail = request.form['userEmail']
    userPassword = request.form['userPassword']
    user = User(email = userEmail, password = userPassword)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('users'))



@app.route('/announcements')
def announcements():
    return render_template('announcements.html')

@app.route('/addAnnouncementPage')
def addAnnouncementPage():
    return render_template('addAnnouncement.html')


@app.route("/addAnnouncement", methods=['POST'])
@login_required
def addAnnouncement():
    title = request.form['title']
    description = request.form['description']
    date = datetime.now()
    #image = request.files['imageUpload']
    announcement = Announcement(title = title, description = description, date = date)
    db.session.add(announcement)
    db.session.commit()
    conn = engine.connect()
    query = "SELECT * from announcement"
    result = conn.execute(query)
    data = result.fetchall()
    return render_template('announcements.html', data = data)


@app.route("/showAnnouncements", methods=['GET'])
def showAnnouncements():
    conn = engine.connect()
    query = "SELECT * from announcement"
    result = conn.execute(query)
    data = result.fetchall()
    #images = [(base64.b64encode(item['image'] for item in result.fetchall()).DATA).encode('ascii')]
    #imagesRaw = [item['image'] for item in result.fetchall()]
    #imagesFormatted = []
    #for x in imagesRaw:
    #    imagesFormatted.append(base64.b64encode(x.DATA))
    return render_template('announcements.html', data = data)



############# FOR TESTING SEARCHBAR #########
@app.route("/searchBarSample")
def searchBarSample():
    return render_template('searchBarSample.html')
#############################################



if __name__ == '__main__':
    app.secret_key = '_5#y2L"F4Q8z\n\xec]/'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = True
    app.run()
