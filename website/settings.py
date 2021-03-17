class DevConfig(object):
    SECRET_KEY = 'your_secret_key'
    CONFIG_TYPE = 'Development'
    WEBSITE_TITLE = 'Comparative Judgements'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI='sqlite:///../data/test_final.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProdConfig(object):
    CONFIG_TYPE = 'Production'
    DB = None
