from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm, PostForm, UpdateForm
from app.models import User, Post
from datetime import datetime


@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = current_user.posts
    return render_template('index.html', title='Home', posts=posts)

@app.route('/about')
@login_required
def about():
    return "about me"


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    time = datetime.utcnow()
    if form.validate_on_submit():
        post = Post(user_id=current_user.id, body=form.body.data)
        db.session.add(post)
        db.session.commit()
        flash('Congratulations, you have successfully created a post!')
        return redirect(url_for('index'))
    return render_template('create.html', title='Create Post', form=form)

@app.route('/delete/<int:id>')
def delete(id):
    post_to_delete = Post.query.get_or_404(id)
    try:
        db.session.delete(post_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return 'There was an issue deleting your post'

@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    post_to_update = Post.query.get_or_404(id)
    form = UpdateForm()
    time = datetime.utcnow()
    if form.validate_on_submit():
        post_to_update.body = form.body.data
        db.session.add(post_to_update)
        db.session.commit()
        flash('Congratulations, you have successfully created a post!')
        return redirect(url_for('index'))
    return render_template('update.html', title='Update Post', form=form, post=post_to_update)