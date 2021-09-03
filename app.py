#!/usr/bin/env python3
from flask import Flask, render_template, url_for, request, redirect, flash, session,logging
import os 
import sqlite3
from data import Challenges
from pathlib import Path
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField
import base64

app = Flask(__name__)
app.secret_key = ''
app.config["IMAGE_UPLOADS"] = "/home/drahoxx/Documents/School/SiteIntePei1/uploads"
challs = Challenges()

#Useful functions
def getUidFromUname(username):
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	uid = cur.execute(f"SELECT uid FROM USERS WHERE username='{username}'").fetchone()
	if uid == None:
		return 0
	return uid[0]
def getUnameFromUid(uid):
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	username = cur.execute(f"SELECT username FROM USERS WHERE uid='{uid}'").fetchone()
	if username == None:
		return "None"
	return username[0]
def getTidFromTname(teamname):
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	tid = cur.execute(f"SELECT tid FROM TEAMS WHERE team_name='{teamname}'").fetchone()
	if tid == None:
		return 0
	return tid[0]
def getTnameFromTid(tid):
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	teamname = cur.execute(f"SELECT team_name FROM TEAMS WHERE tid='{tid}'").fetchone()
	if teamname == None:
		return 'None'
	return teamname[0]

@app.route("/", methods=['GET','POST'])
def index():
	if "username" in session:
		return render_template('home_connected.html')
	if request.method == 'POST':
		#Get form fields
		username = request.form['username']
		password_candidate = request.form['password']
		con = sqlite3.connect('peiIntegration.db')
		cur = con.cursor()
		result = cur.execute(f'SELECT * FROM USERS WHERE username = "{username}"')
		data = cur.fetchone()
		if data != None:
			password = data[4] #GET THE PASSWORD
			if sha256_crypt.verify(password_candidate,password):
				session['logged_in'] = True
				session['username'] = username
				result2 = cur.execute(f'SELECT team_name FROM TEAMS WHERE tid = "{data[6]}"')
				d = result2.fetchone()
				if d != None:
					session['team'] = d[0]
					print(session['team'])
				else:
					session['team'] = 'None' 
				flash('Vous êtes connectés','success')
				return redirect(url_for('challenges'))
			else:
				error = 'Wrong password'
				con.close()
				return render_template('home.html', error=error)
		else:
			error = 'username not found'
			return render_template('home.html', error=error)
	return render_template('home.html')
@app.route("/logout/")
def logout():
	session.clear()
	return redirect(url_for("index"))

@app.route("/about/")
def about():
	return render_template('about.html')


@app.route("/leaderboard/")
def leaderboard():
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	r = cur.execute('SELECT team_name FROM TEAMS')
	teams = r.fetchall()
	#challsxteams=cur.execute("SELECT tid,cid,bonus FROM CHALLxTEAM").fetchall()
	ptsteams=[]
	for t in teams:
		teamname=t[0]
		tid = getTidFromTname(teamname)
		ptsp = cur.execute(f"SELECT SUM(CHALLS.pts)+SUM(CHALLxTEAM.bonus) FROM CHALLS INNER JOIN CHALLxTEAM ON CHALLxTEAM.cid = CHALLS.cid WHERE tid='{tid}'").fetchone()
		if ptsp==None:
			pts=0
		else:
			pts=ptsp[0]
		ptsteams.append([teamname,pts])
	con.close()
	return render_template("leaderboard.html",teams=ptsteams)

@app.route("/latest/", methods=['GET','POST'])
def latest():
	if 'username' not in session:
		flash('Vous devez être connecté pour acceder à cette partie du site','error')
		return redirect(url_for('index'))
	if request.method == 'POST' and 'verifid' in session:
		if request.form.get("y") or request.form.get("n"):
			i = int(bool(request.form.get("y")))
			vid = session['verifid']
			uname = session['username']
			uid = getUidFromUname(uname)
			con = sqlite3.connect('peiIntegration.db')
			cur = con.cursor()
			cur.execute(f"INSERT INTO SVERIF(vid,uid,validate) VALUES('{vid}','{uid}','{i}')")
			con.commit()
			if cur.execute(f'SELECT count(uid) FROM SVERIF WHERE vid="{vid}"').fetchone()[0]>=5:
				r = cur.execute(f"SELECT cid,tid FROM VERIFICATION WHERE vid='{vid}'").fetchone()
				cid=r[0]
				tid=r[1]
				cur.execute(f'DELETE FROM SVERIF WHERE vid={vid}')
				cur.execute(f'DELETE FROM VERIFICATION WHERE vid={vid}')
				cur.execute(f"INSERT INTO CHALLxTEAM(cid,tid) VALUES('{cid}','{tid}')")
				con.commit()
			con.close()
			flash(f'Vous avez voté {"POUR" if i==1 else "CONTRE"} !','success')
			session.pop('verifid')
			return redirect(url_for('latest'))
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	r = cur.execute(f"SELECT vid FROM VERIFICATION EXCEPT SELECT vid FROM SVERIF WHERE uid='{getUidFromUname(session['username'])}'")
	#we get one vid
	vidresult = r.fetchone()
	if vidresult == None:
		return render_template("nothing-to-validate.html")
	vid = vidresult[0]
	#get the cid and teamname and uid of vid
	r = cur.execute(f"SELECT cid,tid FROM VERIFICATION WHERE vid='{vid}'").fetchone()
	cid=r[0]
	tid=r[1]
	teamname=getTnameFromTid(tid)
	path=app.config["IMAGE_UPLOADS"]+f'/{cid}/{teamname}'
	files = os.listdir(path)
	base64Images = []
	for f in files:
		with open(f"{path}/{f}", "rb") as image_file:
			encoded_string = base64.b64encode(image_file.read())
			base64Images.append("data:image/png;base64, "+encoded_string.decode('utf-8'))
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	r = cur.execute(f"SELECT title FROM CHALLS WHERE cid={cid}")
	c = r.fetchone()[0]
	session['verifid']=vid
	return render_template("validate.html",teamname=teamname,base64Images=base64Images,challenge=c)

@app.route("/challenges/")
def challenges():
	return render_template('challenges.html',challenges=challs)


@app.route("/admin/")
def admin():
	return render_template('admin.html')

@app.route("/challenges/<string:id>/", methods=['GET', 'POST'])
def particularChallenge(id):
	#Need to be connected
	print(session)
	if 'username' not in session or session['team']=='None':
		flash("Vous devez être connecté et avoir rejoins une équipe pour acceder à cette partie du site","warning")
		return redirect(url_for("challenges"))
	#Upload
	if request.method == "POST":
		if request.files:
			image = request.files["image"]
			print(image.filename)
			if image.filename.split(".")[1] not in '.jpg .png .jpeg .tif .tiff .bmp .esp .raw .cr2 .nef .orf .sr2' or image.filename=='': #CLAIREMENT PAS OUF (FAILLE DU TYPE FILE UPLOAD DOUBLE EXTENSION)
				flash("Vous devez mettre une image","error")
				return redirect(url_for("challenges"))
			Path(app.config["IMAGE_UPLOADS"]+f'/{id}/{session["team"]}/').mkdir(parents=True, exist_ok=True)
			image.save(os.path.join(app.config["IMAGE_UPLOADS"]+f'/{id}/{session["team"]}', image.filename))
			con = sqlite3.connect('peiIntegration.db')
			cur = con.cursor()
			tid = getTidFromTname(session['team'])
			vidpotential = cur.execute(f'SELECT vid FROM VERIFICATION WHERE cid="{id}" AND tid="{tid}"').fetchone()
			if vidpotential == None:
				cur.execute(f"INSERT INTO VERIFICATION(cid,tid) VALUES('{id}','{tid}')")
				con.commit()
			else:
				vid = vidpotential[0]
				cur.execute(f'DELETE FROM SVERIF WHERE vid={vid}')
				con.commit()
			return redirect(request.url)
	'''
	c={"id":0,"title":"We got an error","desc":"Invalid id", "points":0}
	for ch in challs:
		if ch.get("id")==int(id):
			c=ch
			break
	'''
	con = sqlite3.connect("peiIntegration.db")
	cur = con.cursor()
	datas = cur.execute(f'SELECT * FROM CHALLS WHERE cid="{id}"').fetchone()
	if datas==None:
		flash("Le challenge n'existe pas","error")
		return redirect(url_for("challenges"))
	teams = cur.execute(f"SELECT valDate, TEAMS.team_name FROM TEAMS INNER JOIN CHALLxTEAM ON TEAMS.tid=CHALLxTEAM.tid WHERE cid='{id}'").fetchall()
	return render_template('challenge.html',c = datas,teams=teams)

class RegisterForm(Form):
	fname = StringField('Nom', [validators.Length(min=2, max=50)])
	lname = StringField('Prenom', [validators.Length(min=2, max=50)])
	username = StringField('Username', [validators.Length(min=5, max=50)])
	password = PasswordField('Password', 
		[validators.Length(min=6, max=50),
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Les mots de passe ne sont pas identiques')])
	confirm = PasswordField('Confirmez votre mdp')
	year = RadioField('Année', choices=[('1','1ère année'),('2','2ème année')])

@app.route('/register/', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		lname = form.lname.data
		fname = form.fname.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))
		year = form.year.data
		#Connect to the database
		con = sqlite3.connect('peiIntegration.db')
		cur = con.cursor()
		cur.execute(f"INSERT INTO USERS(fname,lname,username,password,year) VALUES('{fname}','{lname}','{username}','{password}','{year}')")
		con.commit()
		session['logged_in'] = True
		session['username'] = username
		session['team'] = 'None'
		flash('Vous êtes connectés','success')
		return redirect(url_for('challenges'))
	return render_template('register.html', form=form)

@app.route('/teams/', methods=['GET','POST'])
def teams():
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	r = cur.execute('SELECT team_name FROM TEAMS')
	teams = r.fetchall()

	if 'username' not in session:
		error = 'Vous devez être connecté'
		return render_template('teams.html', error=error, teams=teams)
	username = session['username']
	if request.method == 'POST':
		#Get form fields
		teamname = request.form['teamname']
		password_candidate = request.form['password']
		result = cur.execute(f'SELECT * FROM TEAMS WHERE team_name = "{teamname}"')
		data = cur.fetchone()
		if data != None:
			password = data[2] #GET THE PASSWORD
			if password == password_candidate:
				session.clear()
				session['logged_in'] = True
				session['username'] = username
				session['team'] = teamname
				tid=data[0]
				cur.execute(f'UPDATE USERS SET tid="{tid}" WHERE username="{username}"')
				con.commit()
				flash(f"Vous avez rejoin l'équipe {teamname}",'success')
				return redirect(url_for("challenges"))
			else:
				error = 'Wrong password'
				con.close()
				return render_template('teams.html', error=error,teams=teams)
		else:
			cur.execute(f'INSERT INTO TEAMS(team_name,team_password) VALUES("{teamname}","{password_candidate}")')
			con.commit()
			con.close()
			flash("l'équipe a été crée, maintenant rejoignez la")
			return render_template('teams.html', teams=teams)
	con.close()
	return render_template('teams.html',teams=teams)

def dataBaseCreate():
	cur.execute('''CREATE TABLE CHALLS (cid int(10) PRIMARY KEY,title VARCHAR(100),des VARCHAR(1000),pts int(10))''')
	cur.execute('''CREATE TABLE TEAMS (tid INTEGER PRIMARY KEY,team_name VARCHAR(100),team_password VARCHAR(100))''')
	cur.execute('''CREATE TABLE USERS (uid INTEGER PRIMARY KEY,username VARCHAR(100),fname VARCHAR(100),lname VARCHAR(100),password VARCHAR(100),year int(2),tid INTEGER REFERENCES TEAMS(tid),register_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
	cur.execute('''CREATE TABLE CHALLxTEAM (tid INTEGER REFERENCES TEAMS(tid) NOT NULL,cid INTEGER REFERENCES CHALLS(cid) NOT NULL,bonus INTEGER DEFAULT 0,valDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY (tid, cid))''')
	cur.execute('''CREATE TABLE VERIFICATION (vid INTEGER PRIMARY KEY,cid INTEGER REFERENCES CHALLS(cid),tid INTEGER REFERENCES TEAMS(tid))''')
	cur.execute('''CREATE TABLE SVERIF (vid INTEGER REFERENCES VERIFICATION(vid) NOT NULL,uid INTEGER REFERENCES USERS(uid) NOT NULL, validate BOOLEAN,valDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY (vid, uid))''')
	con.commit()
def addChallengesToDB():
	for c in challs:
		print(f"Adding to db: {c.get('id')} : {c.get('title')}")
		cur.execute(f'''INSERT INTO CHALLS VALUES ("{c.get('id')}","{c.get('title')}","{c.get('desc')}","{c.get('points')}")''')
	con.commit()

#If not already created, create the database file and add the challenges to it
if not os.path.isfile(os.path.join(app.config["IMAGE_UPLOADS"]+f'/../', "peiIntegration.db" )):
	con = sqlite3.connect('peiIntegration.db')
	cur = con.cursor()
	dataBaseCreate()
	addChallengesToDB()
	con.close()