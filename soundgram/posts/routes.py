from flask import Blueprint
import os
from flask import flash, request, abort
from flask import render_template  # allows to return HTML renders
from flask import url_for, redirect  # allows attaching static files
from soundgram.models import Post, Comment
from soundgram.posts.forms import PostForm, CommentForm  # importing forms
from soundgram import db
from flask_login import current_user, login_required
from soundgram.users.utils import save_media_file

posts = Blueprint('posts', __name__)

@posts.route("/post/<post_id>", methods=['GET', 'POST'])
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comment_form = CommentForm()
    if comment_form.validate_on_submit():
        comment = Comment(comment=comment_form.comment.data, user_id=current_user.id, post_id=post.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'info')
        return redirect(request.referrer)
    return render_template('posts/post.html', title=post.title, post=post, comment_form=comment_form)


# redirect is not working / how to redirect to previous page?
@posts.route("/comment/<comment_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        abort(403)
    db.session.delete(comment)
    db.session.commit()
    flash('Your comment has been successfuly removed!', 'info')
    return redirect(request.referrer)


#  redirect is not working / how to redirect to previous page?
@posts.route("/comment/<comment_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    form = CommentForm()
    if comment.author != current_user:
        abort(403)
    if form.validate_on_submit():
        comment.comment = form.comment.data
        db.session.commit()
        flash('Your comment has been successfuly edited :)', 'info')
        return redirect(request.referrer)
    elif request.method == 'GET':
        form.comment.data = comment.comment
    return render_template('posts/edit_comment.html', form=form)


@posts.route("/post/<post_id>/edit", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = PostForm()
    if post.author != current_user:
        abort(403)
    if form.validate_on_submit():
        post.title = form.title.data
        post.description = form.description.data
        if form.content.data:
            post.content = save_media_file(form.content.data)
        db.session.commit()
        flash('Your post has been successfuly updated! :)', 'info')
        return redirect(request.referrer)
    elif request.method == 'GET':
        form.title.data = post.title
        form.description.data = post.description
        form.content.data = post.content
    return render_template('posts/edit_post.html', title='Update Post', form=form, legend='Update Post')


@posts.route("/post/<post_id>/delete", methods=['POST', 'GET'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    comment = Comment.query.get(post_id)
    if post.author != current_user:
        abort(403)
    elif comment:
        db.session.delete(comment)
    elif post.content:
        os.remove('soundgram/static/content/' + post.content)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been successfuly removed!', 'info')
    return redirect(url_for('main.home_followed'))


@posts.route('/like/<post_id>/like')
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    current_user.like_post(post)
    db.session.commit()
    flash('You just liked this post', 'info')
    return redirect(request.referrer)


@posts.route('/unlike/<post_id>/unlike')
@login_required
def unlike(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    current_user.unlike_post(post)
    db.session.commit()
    flash('You just unliked this post', 'info')
    return redirect(request.referrer)
