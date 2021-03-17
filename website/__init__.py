import os

from flask import Flask
from website.settings import DevConfig, ProdConfig
from website.extensions import db
from website import views


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    #if os.environ.get('FLASK_ENV') == 'development':
    #    config_object = DevConfig
    #else:
    #    config_object = ProdConfig
    config_object = DevConfig

    app.config.from_object(config_object)
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 10

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    print("!!! Running {} Configuration".format(app.config['CONFIG_TYPE']))

    # Register Extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(views.blueprint)

    return app
