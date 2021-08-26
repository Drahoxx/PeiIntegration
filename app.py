from flask import Flask, render_template, url_for, request, redirect
import os 
from data import Challenges
from pathlib import Path

app = Flask(__name__)
app.config["IMAGE_UPLOADS"] = "/home/drahoxx/Documents/School/SiteIntePei1/uploads"
challs = Challenges()

@app.route("/")
def index():
	return render_template('home.html')

@app.route("/about/")
def about():
	return render_template('about.html')


@app.route("/leaderboard/")
def leaderboard():
	return f"leaderboard"

@app.route("/latest/")
def latest():
	return f"latest"

@app.route("/challenges/")
def challenges():
	return render_template('challenges.html',challenges=challs)


@app.route("/admin/")
def admin():
	return render_template('admin.html')

@app.route("/challenges/<string:id>/", methods=['GET', 'POST'])
def particularChallenge(id):
	#Upload
	if request.method == "POST":
		if request.files:
			image = request.files["image"]
			Path(app.config["IMAGE_UPLOADS"]+f'/{id}').mkdir(parents=True, exist_ok=True)
			image.save(os.path.join(app.config["IMAGE_UPLOADS"]+f'/{id}', image.filename))
			print("Image saved")
			return redirect(request.url)

	c={"id":0,"title":"We got an error","desc":"Invalid id", "points":0}
	for ch in challs:
		if ch.get("id")==int(id):
			c=ch
			break
	return render_template('challenge.html',c = c)
