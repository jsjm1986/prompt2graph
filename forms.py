from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField, TextAreaField, SelectField, FloatField, 
    SubmitField, BooleanField
)
from wtforms.validators import (
    DataRequired, Length, NumberRange, Optional
)

class GraphForm(FlaskForm):
    """图谱创建表单"""
    name = StringField('图谱名称', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('描述', validators=[Optional(), Length(max=500)])
    domain = SelectField('领域', choices=[
        ('tech', '技术栈'),
        ('business', '商业组织'),
        ('academic', '学术研究'),
        ('medical', '医疗诊断'),
        ('legal', '法律案例'),
        ('finance', '金融分析'),
        ('product', '产品开发'),
        ('environment', '环境影响'),
        ('social', '社交网络')
    ], validators=[DataRequired()])
    
    # 输入选项
    file = FileField('上传文件', validators=[
        Optional(),
        FileAllowed(['txt', 'doc', 'docx', 'pdf'], '只允许上传文本文件')
    ])
    text_input = TextAreaField('文本输入')
    
    # 高级选项
    enable_temporal = BooleanField('启用时序关系')
    enable_probabilistic = BooleanField('启用概率关系')
    enable_multi_hop = BooleanField('启用多跳推理')
    confidence_threshold = FloatField('置信度阈值', 
        validators=[Optional(), NumberRange(min=0, max=1)],
        default=0.7
    )
    submit = SubmitField('创建图谱')

class EntityForm(FlaskForm):
    """实体表单"""
    name = StringField('实体名称', validators=[DataRequired()])
    type = StringField('实体类型', validators=[DataRequired()])
    properties = TextAreaField('属性 (JSON)', validators=[Optional()])
    submit = SubmitField('保存实体')

class RelationForm(FlaskForm):
    """关系表单"""
    source = StringField('源实体', validators=[DataRequired()])
    target = StringField('目标实体', validators=[DataRequired()])
    relation_type = StringField('关系类型', validators=[DataRequired()])
    properties = TextAreaField('属性 (JSON)', validators=[Optional()])
    confidence = FloatField('置信度',
        validators=[NumberRange(min=0, max=1)],
        default=1.0
    )
    submit = SubmitField('保存关系')
