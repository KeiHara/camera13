"""
This script runs the application using a development server.
It contains the definition of routes and views for the application.
"""

from flask import Flask, render_template, request, redirect, session, url_for, flash, redirect, session
import pymysql, datetime, os, json, random, calendar, time, datetime
from datetime import datetime, timedelta
from argon2 import PasswordHasher
app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.config['UPLOAD_FOLDER'] = "static/images/"

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

ph = PasswordHasher()

#creating connection to my database
def create_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='13com', 
        charset='utf8mb4'
        ,cursorclass=pymysql.cursors.DictCursor
    )

GUEST = set(['home', 'login', 'signup', 'static', 'layout'])
STUDENT = set(['list', 'home', 'logout', 'claim', 'unclaim', 'profile','resetpass', 'static'])
TEACHER = set(['updateid', 'deleteid'])

@app.before_request
def before_request():

    if request.endpoint not in GUEST and is_logged_in() is False:   
        flash('You have to login', 'alert alert-danger fade-in')
        return redirect(url_for('login'))
    if request.endpoint not in STUDENT and 'role' in session and session['role'] == 1:
        flash('You have to be a teacher or admin to use this page', 'alert alert-danger fade-in')
        return redirect(url_for('home'))
    if request.endpoint in TEACHER and 'role' in session and session['role'] == 2:
        flash('You have to be a an admin to use this page', 'alert alert-danger fadeIn')
        return redirect(url_for('home'))

def redirect_url(default='layout'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html')

 

#list of Resource Type
@app.route("/resourcetype")
def resourcetype():
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT * From `resourcetypes`"
        cursor.execute(sql)
        resourcetypes = cursor.fetchall()
    return render_template('resourcetype.html', title = 'Resource Type', resourcetypes = resourcetypes)

#add resource type
@app.route("/addresourcetype", methods = ["GET", "POST"])
def addresource():
    if request.method == "POST":  
        if (validationResourceType(request.form) is not True):
            flash('Type in the form correctly', 'alert alert-danger fade-in')
            return redirect("addresourcetype")
        else:
        #applying validation
            connection = create_connection()
            with connection.cursor() as cursor:
                sql = "INSERT INTO `resourcetypes` (`ResourceTypeName`) VALUES (%s);"
                val = request.form["ResourceType"]
                cursor.execute(sql, val)
                connection.commit()
                ResourceTypeId = cursor.lastrowid
                connection.close()
            return redirect(url_for("resourcetype"))
    return render_template('addresourcetype.html', title='Add Resource Types')

#delete resource type
@app.route('/resourcetype', methods = ["POST"])
def deleteresource():
    if request.method == "POST":
        ResourceTypeId = int(request.form["ResourceTypeId"])
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "DELETE FROM resourcetypes WHERE ResourceTypeId = %s;"
            vals = (ResourceTypeId)
            cursor.execute(sql, vals)
            connection.commit()
            connection.close()
    flash('Successfully deleted resource type', 'alert alert-success fade-in')
    return redirect(url_for("resourcetype"))





#list of users
@app.route("/users")
def user():
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT `users`.*, `roles`.* FROM `users` LEFT JOIN `roles` ON `users`.`roleid` = `roles`.`RoleId`"
        cursor.execute(sql)
        users = cursor.fetchall()
    return render_template('users.html', title = 'Users', users = users)

#update users info
@app.route("/updateid", methods = ["GET", "POST"])
def updateid():
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM `roles`"
        cursor.execute(sql)
        roles = cursor.fetchall()
    #applying validation
    if request.method == "POST": 
        if (validationUpdateId(request.form) is not True):
            flash('Type in the form correctly', 'alert alert-danger fade-in')
            return redirect("updateid?id="+request.form['id'])
        connection = create_connection()
        with connection.cursor() as cursor:   
            sql = ("""UPDATE `users` SET `username` =    %s, `email` = %s, `roleid`  = %s WHERE `id` = %s;""")
            val = (request.form["username"],request.form["email"], request.form["roleid"], request.form['id'])
            cursor.execute(sql, val)
            connection.commit()
        connection.close()
        return redirect(url_for("user"))
    else:
        connection = create_connection()
        with connection.cursor() as cursor:     
            sql = ("""SELECT * FROM `users` WHERE `id` = %s""")
            val = (request.args["id"])
            cursor.execute(sql, val)
            user = cursor.fetchone()
            if validationExist(user) == False:
                flash('Selected user does not exist', 'alert alert-danger fade-in')
                return redirect(url_for("user"))
        connection.close()
        return render_template('updateid.html', roles = roles , user = user , title='Update Users')

#delete student
@app.route('/deleteid', methods = ["GET", "POST"])
def deleteid():
    if request.method == "GET":
        id = int(request.args['id'])
        connection = create_connection()
        with connection.cursor() as cursor:     
            sql = (""" SELECT * FROM `users` WHERE `id` = %s """)
            val = (id)
            cursor.execute(sql, val)
            user = cursor.fetchone()
            connection.close()
            if validationExist(user) == False:
                flash('Selected user id does not exist', 'alert alert-danger fade-in')
                return redirect(url_for("user"))   
        return render_template('deleteid.html', user = user , title='delete')
    else:
        id = int(request.form["id"])
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s;"
            vals = (id)
            cursor.execute(sql, vals)
            connection.commit()
            connection.close()
    flash('Successfully deleted student', 'alert alert-success fade-in')
    return redirect(url_for("user"))



@app.route('/resetpass', methods = ["GET","POST"])
def resetpass():
    connection = create_connection()
    if request.method == "POST":
        if (validationPassword(request.form) is not True):
            flash('Type in the form correctly', 'alert alert-danger fade-in')
            return redirect("resetpass?id="+request.form['id'])
        with connection.cursor() as cursor: 
            sql = ("""UPDATE `users` SET `password` = %s WHERE `id` = %s;""")
            val = (ph.hash(request.form['resetpass']),request.args["id"])
            cursor.execute(sql, val)
            connection.commit()
            connection.close()
            flash('Password succsesfully changed', 'alert alert-success fade-in')
            return redirect(url_for("home"))
    else:
        connection = create_connection()
        with connection.cursor() as cursor:     
            sql = (""" SELECT * FROM `users` WHERE `id` = %s """)
            val = (request.args['id'])
            cursor.execute(sql, val)
            user = cursor.fetchone()
            connection.close()
            if validationExist(user) == False:
                flash('Selected user id does not exist', 'alert alert-danger fade-in')
                return redirect("home")
        return render_template('resetpass.html', title = 'Reset Password')





#list of Resources
@app.route("/list") 
def list():
    usernames = ""
    connection = create_connection()
    #session('returnUrl')
    with connection.cursor() as cursor:
        sql =  "SELECT `resources`.*, `resourcetypes`.* FROM `resources` LEFT JOIN `resourcetypes` ON `resources`.`ResourceType` = `resourcetypes`.`ResourceTypeId`"
        cursor.execute(sql)
        resources = cursor.fetchall()
    for resource in resources:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM `log` WHERE `log`.`LogResourceId` = '%s' ORDER BY `log`.`LogTime` DESC LIMIT 0, 1"
            cursor.execute(sql, resource['ResourceId'])
            logdata = cursor.fetchone()
            if logdata is not None:
                if logdata['LogReturned'] == 1:
                    resource['Claimed'] = 0 
                    resource['ClaimedBy'] = "NA"
                    resource['DateClaimed'] = "NA"
                else:
                    resource['Claimed'] = 1
                    resource['ClaimedBy'] = logdata['LogUserId']
                    resource['DateClaimed'] = logdata['LogTime']        
                    sql = (""" SELECT username FROM users WHERE id = %s """)
                    cursor.execute(sql,resource['ClaimedBy'])
                    usernames = cursor.fetchone() 
                    print(usernames)
            else:
                resource['Claimed'] = 0 
                resource['ClaimedBy'] =0
                resource['DateClaimed'] = "NA"
    return render_template('list.html', resources = resources, title = 'Resource List', usernames = usernames)

#create Resource
@app.route("/create", methods = ["GET","POST"])
def create():
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM `resourcetypes`"
        cursor.execute(sql)
        resourcetypes = cursor.fetchall()
    if request.method == "POST": 
        #applying validation
        if (validationResource(request.form) is not True):
            flash('Type in the form correctly', 'alert alert-danger fade-in')
            return redirect(url_for("create"))

        else:
            connection = create_connection()
            with connection.cursor() as cursor:
                sql = "INSERT INTO `resources` (`Brand`, `Model`, `PurchaseDate`, `Condition`, `OriginalPrice`, `ResourceType`) VALUES (%s, %s, %s, %s, %s, %s);"
                val = (request.form["Brand"],request.form["Model"],request.form["Purchase"], request.form["Condition"],request.form["Price"], request.form["ResourceType"])
                cursor.execute(sql, val)
                connection.commit()
                ResourceId = cursor.lastrowid
                connection.close()
                #insert an image if the user selected an image
            if 'Picture' in request.files:
                picture = request.files['Picture']
                if picture.filename is not "":
                    picture.filename = str(ResourceId) + "-" + str(calendar.timegm(time.gmtime())) + "." + picture.filename.rsplit('.', 1)[1].lower() #generate new picture name using camera id
                    picture.save(os.path.join(app.config['UPLOAD_FOLDER'], picture.filename))  #save the image in the /static/images file with the new picture name
                    connection = create_connection()
                    with connection.cursor() as cursor:
                        sql = "UPDATE `resources` SET Image=%s WHERE ResourceId = %s"
                        val = (picture.filename, ResourceId)
                        cursor.execute(sql, val)
                        #save or commit values in data base
                        connection.commit()
                        cursor.close()
            return redirect(url_for("list"))
    return render_template('create.html', resourcetypes = resourcetypes, title='Create Resource')

#update resource info
@app.route("/update", methods = ["GET","POST"])
def update():
    connection = create_connection()
    with connection.cursor() as cursor:
        sql = "SELECT * FROM `resourcetypes`"
        cursor.execute(sql)
        resourcetypes = cursor.fetchall()
    #applying validation
    if request.method == "POST": 
        if (validationResource(request.form) is not True):
            flash('Type in the form correctly', 'alert alert-danger fade-in')
            return redirect("update?ResourceId="+request.form['ResourceId'])
        with connection.cursor() as cursor: 
            sql = ("""UPDATE `resources` SET `Brand` = %s, `Model` = %s, `PurchaseDate`  = %s, `Condition`  = %s, `OriginalPrice`  = %s, `ResourceType` = %s WHERE `ResourceId` = %s;""")
            val = (request.form["Brand"],request.form["Model"],request.form["Purchase"], request.form["Condition"],request.form["Price"], request.form["ResourceType"], request.form["ResourceId"])
            cursor.execute(sql, val)
            connection.commit()
            connection.close()
        deleteImage(request.form['ResourceId'])
        #updates the image if the user selected new image
        if 'Picture' in request.files:
            picture = request.files['Picture']
            if picture.filename is not "": 
                picture.filename = str(request.form['ResourceId']) + "-" + str(calendar.timegm(time.gmtime())) + "." + picture.filename.rsplit('.', 1)[1].lower() #generate new picture name using resource id
                picture.save(os.path.join(app.config['UPLOAD_FOLDER'], picture.filename))  #save the image in the /static/images file with the new picture name
                connection = create_connection()
                with connection.cursor() as cursor:
                    sql = "UPDATE `resources` SET Image=%s WHERE ResourceId = %s"
                    val = (picture.filename, request.form['ResourceId'])
                    cursor.execute(sql, val)
                    #save or commit values in data base
                    connection.commit()
                    cursor.close()
            return redirect(url_for("list"))
    else:
        connection = create_connection()
        with connection.cursor() as cursor:     
            sql = (""" SELECT * FROM `resources` WHERE `ResourceId` = %s """)
            val = (request.args['ResourceId'])
            cursor.execute(sql, val)
            resource = cursor.fetchone()
            connection.close()
            if validationExist(resource) == False:
                flash('Selected resource id does not exist', 'alert alert-danger fade-in')
                return redirect(url_for("list"))
        return render_template('update.html', resourcetypes = resourcetypes, resource = resource , title='update')

# Delete Resource from the database
@app.route('/delete', methods = ["GET", "POST"])
def delete():
    if request.method == "GET":
        ResourceId = int(request.args['ResourceId'])
        connection = create_connection()
        with connection.cursor() as cursor:     
            sql = (""" SELECT * FROM `resources` WHERE `ResourceId` = %s """)
            val = (ResourceId)
            cursor.execute(sql, val)
            resource = cursor.fetchone()
            connection.close()
            print(resource)
            if validationExist(resource) == False:
                flash('Selected resource id does not exist', 'alert alert-danger fade-in')
                return redirect(url_for("list"))   
        return render_template('delete.html', resource = resource , title='delete')
    else:
        ResourceId = int(request.form["ResourceId"])
        deleteImage(ResourceId)
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = "DELETE FROM resources WHERE ResourceId = %s"
            vals = (ResourceId)
            cursor.execute(sql, vals)
            connection.commit()
            connection.close()
    flash('Successfully deleted resource', 'alert alert-success fade-in')
    return redirect(url_for("list"))

#deletes an image from database
def deleteImage(ResourceId):
    connection = create_connection()
    with connection.cursor() as cursor:     
        sql = (""" SELECT * FROM `resources` WHERE `ResourceId` = %s """)
        val = (ResourceId)
        cursor.execute(sql, val)
        resource = cursor.fetchone()
        connection.close()
    if resource['Image'] is not "":
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], resource['Image']))
        except:
            print("file already deleted")
        finally:
            connection = create_connection()
            with connection.cursor() as cursor:
                sql = "UPDATE `resources` SET Image=%s WHERE ResourceId = %s"
                val = ("", ResourceId)
                cursor.execute(sql, val)
                #save or commit values in data base
                connection.commit()
                cursor.close()

#Claim Camera
@app.route('/claim', methods=  ["GET", "POST"])
def claim():
    if request.method == "GET":
        ResourceId = int(request.args['ResourceId'])
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = ('SELECT * FROM resources WHERE resourceid = %s')
            val = ResourceId
            cursor.execute(sql,val)
            resource = cursor.fetchone()
            if validationExist(resource) == False:
                flash('Selected resource id does not exist', 'alert alert-danger fade-in')
                return redirect(url_for("list"))
            sql = """INSERT INTO `log` (`LogUserId`,`LogResourceId`) VALUES (%s,%s)"""
            vals = (session['id'], ResourceId)
            cursor.execute(sql,vals)
            connection.commit()
            connection.close()
    flash('Resource claimed', 'alert alert-success fade-in')
    return redirect(url_for("list"))
#Unclaim Camera
@app.route('/unclaim', methods=  ["GET", "POST"])   
def unclaim():
    if request.method == "GET":
        ResourceId = int(request.args['ResourceId'])
        connection = create_connection()
        with connection.cursor() as cursor:
            sql = ('SELECT * FROM log WHERE LogUserId = %s AND LogResourceId = %s')
            val = (session['id'],ResourceId)
            cursor.execute(sql,val)
            log = cursor.fetchone()
            if validationExist(log) == False:
                flash('Selected resource id does not exist', 'alert alert-danger fade-in')
                return redirect(url_for("list"))
            sql = "UPDATE `log` SET LogReturned = 1 WHERE LogUserId  = %s AND LogResourceId = %s"
            vals = (session['id'],ResourceId)
            cursor.execute(sql,vals)
            connection.commit()
            connection.close()
        #session(['returnUrl' => url() -> previous()]);
    flash('Resource returned', 'alert alert-success fade-in')
    return redirect(redirect_url())








#login page
@app.route("/login", methods= ["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form['password']
        connection = create_connection()
        with connection.cursor() as cursor:
            # get how many rows the database can find that match the criteria
            sql = ('SELECT * FROM users WHERE username = %s')
            val = (str(request.form['username']))
            cursor.execute(sql,val)
            account = cursor.fetchall()
            # check if there are row/s that match the criteria
            try:
                ph.verify(account[0]["password"], password)    
                # Create session data, we can access this data in other routes
                session['logged_in'] = True
                session['id'] = account[0]['id']
                session['role'] = account[0]['roleid']
                session['username'] = account[0]['username']
                flash('Logged in as ' + request.form['username'], 'alert alert-success fade-in')
                return redirect(url_for("list"))
            except:
                flash('Incorrect username or password', 'alert alert-danger')
                return redirect(url_for("login"))
    return render_template('login.html', title='Login')

#login function
def is_logged_in():
    return 'logged_in' in session

#logout function
@app.route("/logout")
def logout():
    #Remove session data
    session.pop('logged_in', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
   # Redirect to login page
    flash('successfully logged out', 'alert alert-success fade-in')
    return redirect(url_for('login'))



#signup page
@app.route("/signup", methods= ["GET", "POST"])
def signup():
    connection = create_connection()
    if request.method == "POST": 
        try:
            username = request.form['username']
            email = request.form['email']
            if username == "" or email == "":
                flash('Please enter username', 'alert alert-danger fade-in')
                return redirect(url_for('signup'))

            connection = create_connection()
            with connection.cursor() as cursor:
                hash = ph.hash(request.form['password'])
                sql = "INSERT INTO `users` (`username`, `email`, `password`) VALUES (%s, %s, %s);"
                val = (request.form["username"],request.form["email"],hash)
                cursor.execute(sql, val)
                connection.commit()
                cameraId = cursor.lastrowid
        except pymysql.IntegrityError as e: 
            if e.args[0] == 1062:
                flash('duplicated email or username', 'alert alert-danger fade-in')
                return redirect(url_for('signup'))
            
        finally:
            connection.close()
        flash('A user is created for ' + request.form["username"], 'alert alert-success fade-in')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Signup')   

#profile
@app.route("/profile", methods= ["GET", "POST"])
def profile():
    #session('returnUrl')
    if request.method == "GET":
        id = int(request.args['userid'])
        if session['id'] != id:
            flash('Do not stalk other people', 'alert alert-danger fade-in')
            return redirect(url_for("home"))
        else:
            connection = create_connection()
            with connection.cursor() as cursor:
                sql = ("""SELECT `users`.*, `roles`.* FROM `users` LEFT JOIN `roles` ON `users`.`roleid` = `roles`.`RoleId` WHERE `id` = %s""")
                val = (id)
                cursor.execute(sql, val)
                user = cursor.fetchone()
                sql = ("""SELECT `resources`.*, `log`.*  FROM `resources` LEFT JOIN `log` ON `resources`.`ResourceId` = `log`.`LogResourceId` WHERE `LogUserId` = %s AND `LogReturned` = 0""")
                val = (id)
                cursor.execute(sql, val)
                resources = cursor.fetchall()
                connection.close()  
                print(resources)
    return render_template('profile.html', resources = resources , user = user , title='Profile')






#server side validation 
def validationResource(form):
    present = datetime.now()
    try:
        if len(form["Brand"]) <2 or len(form["Model"]) <2 or len(form["Condition"]) <2 or len(form["Brand"]) <2 or form["ResourceType"] == None:
            raise Exception("Bad Id")
        if float(form["Price"]) < 0:
            raise Exception("Bad Id")
    except:
        return False
    return True    

def validationUpdateId(form):
    try:
        if len(form["username"]) <2 or len(form["email"]) <2 or form["roleid"] == None:
            raise Exception("Bad Id")
    except:
        return False
    return True

def validationResourceType(form):
    try:
        if len(form["ResourceType"]) <2:
            raise Exception("Bad Id")
    except:
        return False
    return True

def validationPassword(form):
    try:
        if len(form["resetpass"]) <2:
            raise Exception("Bad Id")
    except:
        return False
    return True

def validationExist(dic):
    if dic == None:
        return False

@app.errorhandler(404)
def page_not_found(e):
    flash('Url does not exist', 'alert alert-danger fade-in')
    return redirect(redirect_url("home"))

    
if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT, debug = True)
