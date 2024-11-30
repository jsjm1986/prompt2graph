from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import config
from models import db
from auth import auth, login_manager
import os

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    JWTManager(app)

    # 注册蓝图
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from graph import graph as graph_blueprint
    app.register_blueprint(graph_blueprint, url_prefix='/graph')

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
