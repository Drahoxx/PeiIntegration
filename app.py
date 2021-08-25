from flask import Flask, render_template, url_for
from data import Challenges

app = Flask(__name__)

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

@app.route("/challenges/<string:id>/")
def particularChallenge(id):
	return render_template('challenge.html',id=id)