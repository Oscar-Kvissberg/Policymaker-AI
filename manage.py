from flask.cli import FlaskGroup
from main import app, db, initialize_app
from flask_migrate import Migrate

migrate = Migrate(app, db)

cli = FlaskGroup(app)

@cli.command("init")
def init():
    initialize_app()
    print("Application initialized")

@cli.command("update_db")
def update_db():
    with app.app_context():
        db.create_all()
    print("Database updated")

if __name__ == '__main__':
    cli()