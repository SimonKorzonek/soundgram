from flask import Blueprint, url_for, redirect, render_template, flash, request
from datetime import datetime
from soundgram.models import User, Post, Message
from soundgram.users.forms import RegForm, LogForm, ForgotForm, UpdateAccountForm, ResetPasswordForm, MessageForm
from soundgram.posts.forms import CommentForm
from soundgram.users.utils import save_picture, send_reset_email
from soundgram import db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required


users = Blueprint('users', __name__)

@users.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    messages = current_user.messages_received.order_by(Message.timestamp.desc())
    return render_template('user/messages.html', messages=messages)

@users.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    message_form = MessageForm()
    if message_form.validate_on_submit():
        msg = Message(author=current_user, recipient=user, body=message_form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.')
        return redirect(url_for('main.home_newest', username=recipient))
    return render_template('user/message.html', title=('Send Message'), message_form=message_form, recipient=recipient)


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home_newest'))
    register_form = RegForm()
    if register_form.validate_on_submit() and register_form.register.data:
        hashed_password = bcrypt.generate_password_hash(register_form.password.data).decode('utf=8')  # decode - to convert bytes to string
        user = User(username=register_form.username.data, email=register_form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!', 'info')
        return redirect(url_for('users.login'))
    return render_template('user/register.html', title='Login', register_form=register_form)


@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home_newest'))
    login_form = LogForm()
    if login_form.validate_on_submit() and login_form.login.data:
        user = User.query.filter_by(email=login_form.email.data).first()  # checking if user with given email exists in out db. If he does, we're grabbing the first one, if not if returns "none"
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):  # if user exists in db, and password is valid
            login_user(user, remember=login_form.remember.data)
            return redirect(url_for('main.home_followed'))
        else:
            flash('E-mail or password incorrect. Try again', 'danger')
    return render_template('user/login.html', title='Login', login_form=login_form)


@users.route("/user/<username>", methods=['GET', 'POST'])
@login_required
def user_profile(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    comment_form = CommentForm()
    return render_template('user/user_profile.html', posts=posts, user=user, comment_form=comment_form)


@users.route("/user/<username>/edit_profile", methods=['GET', 'POST'])
@login_required
def edit_profile(username):
    form = UpdateAccountForm()
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated!', 'info')
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('user/edit_profile.html', posts=posts, user=user, form=form, image_file=image_file)


@users.route("/follow/<username>")
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.home_newest'))
    if user == current_user:
        flash('You cannot follow yourself!')
        return redirect(url_for('users.user_profile', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You started following {}!'.format(username), 'info')
    return redirect(request.referrer)


@users.route("/unfollow/<username>")
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.home'))
    if user == current_user:
        flash('You cannot unfollow yourself!')
        return redirect(url_for('users.user_profile', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('You stopped following {}.'.format(username), 'info')
    return redirect(request.referrer)


@users.route("/user/<username>/followed_by")
@login_required
def followed_by(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('user/user_list.html', user=user, page=page, posts=posts)


@users.route("/user/<username>/is_following")
@login_required
def is_following(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page, per_page=2)
    return render_template('user/user_list.html', user=user, page=page, posts=posts)


@users.route("/forgot")
def forgot():
    form = ForgotForm()
    return render_template('user/forgot.html', title='Forgot', form=form)


@users.route("/logout")
def logout():
    logout_user()
    flash("You've just logged out", 'success')
    return redirect(url_for('users.login'))


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home_newest'))
    form = ForgotForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('user/reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'info')
        return redirect(url_for('users.login'))
    return render_template('user/reset_token.html', title='Reset Password', form=form)
