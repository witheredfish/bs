import datetime
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from formencode import validators


class AttributeValidator:

    def __init__(self, value):
        self.value = value

    def validate_int(self):
        try:
            validate = validators.Int()
            validate.to_python(self.value)
        except:
            raise ValidationError(
                f'{self.value}，值必须为int类型'
            )

    def validate_float(self):
        try:
            validate = validators.Number()
            validate.to_python(self.value)
        except:
            raise ValidationError(
                f'{self.value}，值必须为float类型'
            )

    def validate_yes_no(self):
        try:
            validate = validators.OneOf(['是', '否'])
            validate.to_python(self.value)
        except:
            raise ValidationError(
                f'{self.value}，值必须为“是”或“否”'
            )

    def validate_yes_no(self):
        try:
            datetime.datetime.strptime(self.value.strip(), "%Y.%m.%d")
        except:
            raise ValidationError(
                f'{self.value}，值必须为YYYY.MM.DD的格式'
            )
