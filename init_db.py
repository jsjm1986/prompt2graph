from app import create_app
from models import db

def init_db():
    """初始化数据库"""
    app = create_app()
    with app.app_context():
        # 删除所有表
        db.drop_all()
        # 创建所有表
        db.create_all()
        print("数据库初始化完成！")

if __name__ == '__main__':
    init_db()
