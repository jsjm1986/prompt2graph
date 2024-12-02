from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from config import config
from models import db
import os

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    from graph import graph as graph_blueprint
    app.register_blueprint(graph_blueprint, url_prefix='/graph')

    # 根路由
    @app.route('/')
    def index():
        return redirect(url_for('graph.my_graphs'))

    # 创建数据库表
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
