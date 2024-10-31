from app_init import app, custom_cli
from flask.cli import FlaskGroup

cli = FlaskGroup(app)
app.cli.add_command(custom_cli)

if __name__ == '__main__':
    cli()