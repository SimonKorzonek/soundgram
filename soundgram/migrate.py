from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from flask_sqlalchemy import SQLAlchemy
from soundgram import create_app


app = create_app()
db = SQLAlchemy(app)

migrate = Migrate(app, db)
script_manager = Manager(app)

script_manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    script_manager.run()
