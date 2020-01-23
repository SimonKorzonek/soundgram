from flask import Blueprint
from flask import flash, request
from flask import render_template
from flask import redirect
from soundgram.models import Post
from soundgram.posts.forms import PostForm, CommentForm
from soundgram.users.utils import save_media_file
from soundgram import db
from flask_login import current_user, login_required

main = Blueprint('main', __name__)


@main.route("/")
@main.route("/home_newest", methods=['GET', 'POST'])
@login_required
def home_newest():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    post_form = PostForm()

    if post_form.validate_on_submit():
        if post_form.content.data:
            content_file = save_media_file(post_form.content.data)
            post = Post(title=post_form.title.data, description=post_form.description.data, content=content_file, author=current_user)
        else:
            post = Post(title=post_form.title.data, description=post_form.description.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'info')
        return redirect(request.referrer)
    return render_template('main/home.html', title='Newest posts', post_form=post_form, posts=posts)


@main.route("/")
@main.route("/home_followed", methods=['GET', 'POST'])
@login_required
def home_followed():
    page = request.args.get('page', 1, type=int)
    user = current_user
    posts = user.followed_posts().order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    post_form = PostForm()
    if post_form.validate_on_submit():
        content_file = save_media_file(post_form.content.data)
        post = Post(title=post_form.title.data, description=post_form.description.data, content=content_file, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'info')
        return redirect(request.referrer)
    return render_template('main/home.html', title='Followed posts', post_form=post_form, posts=posts)


@main.route("/about")
def about():
    return render_template('main/about.html', title='About')
