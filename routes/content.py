from flask import Blueprint, render_template

content = Blueprint('content', __name__, template_folder="../templates")

@content.route("/login")
def login_page():
    return render_template("login.j2")