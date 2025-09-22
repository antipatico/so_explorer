from flask import Flask, render_template, request
from so_explorer.cli import symbols_summary, symbols_search, symbol_get, sofile_get

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("template.html", symbols=symbols_summary(session))


@app.route("/search", methods=["POST"])
def search():
    return render_template(
        "template.html", symbols=symbols_search(session, request.form["search"])
    )


@app.route("/symbol")
def show_symbol():
    sym = request.args.get("sym", "")
    return render_template("template.html", symbol=sym, xrefs=symbol_get(session, sym))


@app.route("/sofile")
def sofile():
    id = request.args.get("id", "")
    return render_template("template.html", sofile=sofile_get(session, id))


def run(s):
    global session
    session = s
    app.run()
