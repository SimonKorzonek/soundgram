from datetime import datetime
from soundgram import db, login_manager
from flask import current_app
from flask_login import UserMixin  # provides methods required to user autentication - is authenticated, is active, is anonymus, get id
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

# it's needed for login_manager to work - have to know how to grab users by thoir id's
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#  association followers table
followers = db.Table('followers', db.Column('follower_id', db.Integer, db.ForeignKey('user.id')), db.Column('followed_id', db.Integer, db.ForeignKey('user.id')))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)  # post sets additional query in the background, that will get all posts user created, it is not declaration of new column
    bio = db.Column(db.String(120), nullable=True)

    # relationship between users in followers table
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic')

    #  relationships beetweend posts comments and likes
    post = db.relationship(
        'Post',
        backref='author',
        lazy=True)  # backhref adds column to post model by reference to another class    # lazy loads the data as necesary at one go --- author - db feature - we havent declared any author, though, python will understand
    comment = db.relationship(
        'Comment',
        backref='author',
        lazy=True)
    liked = db.relationship(
        'Likes',
        foreign_keys='Likes.user_id',
        backref='user',
        lazy='dynamic')

    #  message relationships
    messages_sent = db.relationship(
        'Message',
        foreign_keys='Message.sender_id',
        backref='author',
        lazy='dynamic')
    messages_received = db.relationship(
        'Message',
        foreign_keys='Message.recipient_id',
        backref='recipient',
        lazy='dynamic')
    last_message_read_time = db.Column(db.DateTime)

    #  user object behaviors
    def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()

    def like_post(self, post):
        if not self.has_liked_post(post):
            like = Likes(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def unlike_post(self, post):
        if self.has_liked_post(post):
            Likes.query.filter_by(
                user_id=self.id,
                post_id=post.id).delete()

    def has_liked_post(self, post):
        return Likes.query.filter(
            Likes.user_id == self.id,
            Likes.post_id == post.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own)
        # union combines two things before sorting the posts in return of function

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod  # if token is valid this will return user fitting token
    def verify_reset_token(token, user_id):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)[user_id]
        except Exception:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}', '{self.messages_received}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)  # utcnow without (), because we wanna pass function, not the current time
    content = db.Column(db.String(60), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # user.id lowercase in case of refering just id, not whole class
    comments = db.relationship('Comment', backref='title', lazy='dynamic')

    likes = db.relationship('Likes', backref='post', lazy='dynamic')

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}', '{self.content}')"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(140))
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)

    def __repr__(self):
        return f"Comment('{self.comment}', '{self.date_posted}')"

class Likes(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)
