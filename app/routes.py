from flask import render_template, flash, redirect, url_for, request
import datetime
from app import app, db
from app.forms import RegistrationForm, LoginForm, EditProfileForm, CreatePostForm, AddCommentForm, SearchForm, SendMessageForm
from app.models import User, Post, Comment, Like, Message
from flask_login import current_user, login_user, logout_user, login_required
import os
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename
from flask import current_app
from config import ALLOWED_EXTENSIONS, BEARCORD_TOKEN


def checkAllowedExtensions(file: str):
    print(file)
    if "." in file:
        extension = file.split(".")[-1]
        print(extension)
        if extension in ALLOWED_EXTENSIONS:
            return True
    return False


def save_uploaded_file(form_field, folder_name, success_msg="Файл загружен!", error_msg=None):
    if not form_field.data:
        return None

    file = form_field.data

    if not checkAllowedExtensions(file.filename):
        if error_msg is None:
            error_msg = f"Ошибка: неверный тип файла (разрешены {ALLOWED_EXTENSIONS})"
        flash(error_msg, "danger")
        return None

    filename = secure_filename(f"{current_user.id}_{file.filename}")
    upload_folder = os.path.join(current_app.root_path, "..", "static", folder_name)
    os.makedirs(upload_folder, exist_ok=True)
    file.save(os.path.join(upload_folder, filename))

    flash(success_msg, "success")
    print(os.path.join(upload_folder, filename))
    return filename


@app.route('/')
def index():
    return render_template("index.html", posts=Post.query.all(), comment_form=AddCommentForm())


@app.route('/bearcord_auth')
def bearcord_auth():
    return render_template('bearcord_auth.html')


@app.route('/bearcord_login/<string:username>/<string:password>/<string:token>', methods=['GET', 'POST'])
def bearcord_login(username, password, token):

    if token != BEARCORD_TOKEN:
        return "Невверный токен!"

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    print(f"{username} {password}")

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password(password):
        return "Неверные данные! <a href='/'>Назад</a>"

    login_user(user, remember=False)
    flash(f'Добро пожаловать, {user.username}!', 'success')

    next_page = request.args.get('next')
    if not next_page or not next_page.startswith('/'):
        next_page = url_for('index')
        return redirect(next_page)

    return "Нету данных"


@app.route('/bearcord_register/<string:username>/<string:password>/<string:token>', methods=['GET', 'POST'])
def bearcord_register(username, password, token):
    if token != BEARCORD_TOKEN:
        return "Неверный токен!", 403

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if User.query.filter_by(username=username).first():
        return redirect(url_for('bearcord_login', username=username, password=password, token=token))

    user = User(username=username)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return redirect(url_for('bearcord_login', username=username, password=password, token=token))

    login_user(user)
    return redirect(url_for('index'))


@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    createpostform = CreatePostForm()
    if createpostform.validate_on_submit():
        filename = save_uploaded_file(
            createpostform.image,
            "posts",
            success_msg="Картинка загружена!"
        )
        if createpostform.image.data and filename is None:
            return redirect(url_for("create_post"))

        post = Post(
            content=createpostform.content.data,
            image=filename,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash("Пост опубликован", "success")
        return redirect(url_for("index"))
    print(Post.query.all())
    return render_template('create_post.html', title="Создать пост", form=createpostform)



@app.route('/add_cooment/<int:post_id>', methods=['GET', 'POST'])
@login_required
def add_comment(post_id):
    addcommentform = AddCommentForm()
    post = Post.query.get_or_404(post_id)
    if addcommentform.validate_on_submit():
        
        if addcommentform.content.data is None:
            return redirect(url_for("add_comment"))

        comment = Comment(
            content=addcommentform.content.data,
            author=current_user,
            post=post
        )

        db.session.add(comment)
        db.session.commit()
        flash("Комментарий опубликован", "success")
    return redirect(url_for("index"))


@app.route('/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)

    like = Like.query.filter_by(
        userId=current_user.id,
        postID=post.id
    ).first()

    if like:
        db.session.delete(like)
    else:
        like = Like(user=current_user, post=post)
        db.session.add(like)

    db.session.commit()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
@login_required
def search():
    searchform = SearchForm(request.args)
    users = []
    query = searchform.query.data
    if query:
        users = User.query.filter(
            User.username.ilike(f'%{query}%')
        ).all()
    return render_template('search.html', users=users, form=searchform)
    

@app.route('/chat/<string:username>', methods=['GET','POST'])
@login_required
def chat(username):
    user = User.query.filter_by(
                username=username
            ).first_or_404()


    
    if user.id == current_user.id:
        flash("Вы не можете писать самому себе!", "warning")
        return redirect(url_for("index"))

    sendmessageform = SendMessageForm()

    if sendmessageform.validate_on_submit():
        message = Message(content=sendmessageform.content.data, sender_id=current_user.id, recipient_id=user.id)
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('chat', username=username))
    
        
    messages = Message.query.filter(
        ((Message.sender == current_user) & (Message.recipient == user)) | ((Message.sender == user) & (Message.recipient == current_user))
    ).order_by(Message.timestamp).all()


    return render_template('chat.html', messages=messages, user=user, form=sendmessageform)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    editprofileform = EditProfileForm()
    if editprofileform.validate_on_submit():
        filename = save_uploaded_file(
            editprofileform.avatar,
            "avatars",
            success_msg="Аватарка успешно обновлена!"
        )
        if filename:
            current_user.avatar = filename
            db.session.commit()
            return redirect('profile')
    return render_template('profile.html', title="Профиль", form=editprofileform)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    loginform = LoginForm()

    if loginform.validate_on_submit():
        user = User.query.filter_by(username=loginform.username.data).first()

        if user is None or not user.check_password(loginform.password.data):
            flash('Неверное имя пользователя или пароль', 'danger')
            return redirect(url_for('login'))

        login_user(user, remember=False)
        flash(f'Добро пожаловать, {user.username}!', 'success')

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        return redirect(next_page)

    return render_template("login.html", title="Вход", form=loginform)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    registrationform = RegistrationForm()

    if registrationform.validate_on_submit():
        user = User(username=registrationform.username.data)
        user.set_password(registrationform.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Вы успешно зарегистрировались!", 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title="Регистрация", form=registrationform)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))