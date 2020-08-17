from flask import Flask, render_template
from so_explorer import symbols_summary

app = Flask(__name__)

@app.route('/')
def index():
	return render_template("template.html", symbols=symbols_summary(session))

def run(s):
	global session
	session = s
	app.run()