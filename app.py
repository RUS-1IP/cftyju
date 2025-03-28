
import os
import base64


from fileinput import filename
from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g, make_response, send_from_directory
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from flask_migrate import Migrate
from db import *
from forms import LoginForm, RegisterForm
from UserLogin import UserLogin
from admin.admin import admin

# конфигурация
DATABASE = '/tmp/flask.db'
DEBUG = True
SECRET_KEY = '6Ld2POEqAAAAAPS0gPYLoxqVwawpRY5uuhhd5bBx'
USERNAME = 'admin'
PASSWORD = '123'


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(app.root_path, "flask.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI' # Ключ сайта
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
app.config['RECAPTCHA_OPTIONS'] = {"theme" : "light"}
app.app_context().push()
db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(admin, url_prefix='/admin')
# game_folder = f'{app.static_folder}/games'


login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Авторизуйтесь для доступа к закрытым страницам"
login_manager.login_message_category = "success"



@app.before_request
def create_table():
    if not hasattr(g, '_tables_created'):
        db.create_all()
        g._tables_created = True

@app.template_filter('b64encode')
def b64encode(data):
    if data is None:
        return ''
    return base64.b64encode(data).decode('utf-8')

@login_manager.user_loader
def load_user(user_id):
    return UserLogin().fromDB(user_id, db.session)

@app.route("/")
def index():
    menu = MainMenu.query.all()
    posts = Posts.query.all()
    return render_template('index.html', title="Про Flask", menu=menu,  posts=posts, user=current_user)



@app.route('/about')
def about():
    menu = MainMenu.query.all()
    print(url_for('about'))
    return render_template('about.html', title="О сайте", menu=menu)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('page404.html', title='Страница не найдена', menu=MainMenu.query.all())

@app.errorhandler(401)
def page_not_found(error):
    return render_template('page401.html', title='Не авторизованный пользователь', menu=MainMenu.query.all())
@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.psw, form.psw.data):
            userlogin = UserLogin().create(user)
            login_user(userlogin, remember=form.remember.data)
            return redirect(request.args.get("next") or url_for("profile"))

        flash("Неверная пара логин/пароль", "error")


    return render_template("login.html", menu=MainMenu.query.all(), title="Авторизация", form=form)




@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
            hash_psw = generate_password_hash(form.psw.data)
            new_user = Users(name = form.name.data, email = form.email.data, psw = hash_psw, time=int(datetime.now().timestamp()))
            db.session.add(new_user)
            db.session.commit()
            flash("Вы успешно зарегистрированы", "success")
            return redirect(url_for('login'))


    return render_template("register.html", menu=MainMenu.query.all(), title="Регистрация", form=form)


@app.route('/listgames', methods=['POST', 'GET'])
def listgames():
    menu = MainMenu.query.all()
    try:
        games = Games.query.all()
    except Exception as e:
        flash(f'Ошибка получения списка игр: {str(e)}', 'error')
        games = []
    return render_template('listgames.html', title='Список игр', menu=menu, games=games)


@app.route("/game/<int:game_id>")
@login_required
def game(game_id):
    game = Games.query.get_or_404(game_id)
    menu = MainMenu.query.all()
    response = make_response(render_template('game.html', menu=menu, title=game.title, game=game))
    response.set_cookie('game_path', game.link, path='/', samesite='Lax')
    return response

@app.route('/pygame')
@login_required
def pygame():
    game_path = f'games/{request.cookies.get("game_path") }/build/web'
    return send_from_directory(os.path.join(app.static_folder, game_path), 'index.html')

@app.route('/<path:path>')
@login_required
def game_static_files(path):
    return send_from_directory(os.path.join(app.static_folder, f'games/{path.removesuffix(".apk")}/build/web'), path)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта", "success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template("profile.html", menu=MainMenu.query.all(), title="Профиль")

@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if img:
        h = make_response(img)
        h.headers['Content-Type'] = 'image/png'
        return h
    return ''

@app.route('/upload', methods=["POST", "GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                success = Users.updateUserAvatar(img, current_user.get_id())
                if not success:
                    flash("Ошибка обновления аватара", "error")
                else:
                    flash("Аватар обновлен", "success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла", "error")
        else:
            flash("Ошибка обновления аватара", "error")

    return redirect(url_for('profile'))
@app.route('/game/<int:game_id>/comments')
def get_comments(game_id):
    comments = Comments.query.filter_by(game_id=game_id, parent_id = None).order_by(Comments.timestamp.desc()).all()
    current_user_id = int(current_user.get_id())

    def serialize_comment(comment):
        return {
                "id": comment.id,
                "user": comment.user.name,
                "avatar": f'data:image/png;base64, {base64.b64encode(comment.user.avatar).decode("utf-8")}' if comment.user.avatar else None,
                "text": comment.text,
                "timestamp": comment.timestamp.strftime('%Y-%m-%d %H:%M'),
                "likes": comment.likes,
                "is_owner": comment.user_id == current_user_id,
                'replies': [serialize_comment(reply) for reply in comment.replies]
            }
    comments_data = [serialize_comment(comment) for comment in comments]
    return {"comments":comments_data}

@app.route('/game/<int:game_id>/comment', methods=['POST'])
@login_required
def add_comment(game_id):
    data = request.json
    text = data.get('text', '').strip()
    parent_id = data.get('parent_id')  # ID родительского комментария (если есть)

    if not text:
        return {"error": "Комментарий не может быть пустым"}, 400

    comment = Comments(
        user_id=current_user.get_id(),
        game_id=game_id,
        text=text,
        parent_id=parent_id  # Привязываем к родительскому комментарию
    )
    db.session.add(comment)
    db.session.commit()
    return {"message": "Комментарий добавлен"}

@app.route('/comment/<int:comment_id>/like', methods=["POST"])
@login_required
def like_comment(comment_id):
    comment = Comments.query.get_or_404(comment_id)
    existing_like = CommentLikes.query.filter_by(user_id = current_user.get_id(), comment_id = comment_id).first()
    if existing_like:
        db.session.delete(existing_like)
        comment.likes -=1
    else:
        new_like = CommentLikes(user_id = current_user.get_id(), comment_id = comment_id)
        db.session.add(new_like)
        comment.likes += 1
    db.session.commit()
    return {'likes':comment.likes}
@app.route('/comment/<int:comment_id>/delete', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comments.query.get_or_404(comment_id)
    if comment.user_id != int(current_user.get_id()):
        return {'error': "Вы можете удалять только свои комментарии"}, 403
    CommentLikes.query.filter_by(comment_id=comment_id).delete()
    db.session.delete(comment)
    db.session.commit()
    return {'success': True}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)