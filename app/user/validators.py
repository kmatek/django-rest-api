import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class UppercaseValidator:
    def validate(self, password, user=None):
        if not re.findall('[A-Z]', password):
            raise ValidationError(
                _("This password must contain at" +
                  " least 1 uppercase letter, A-Z."),
                code='password_no_upper')

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 uppercase letter, A-Z.")


class LowercaseValidator:
    def validate(self, password, user=None):
        if not re.findall('[a-z]', password):
            raise ValidationError(
                _("This password must contain at" +
                  " least 1 lowercase letter, a-z."),
                code='password_no_lower')

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 lowercase letter, a-z.")


class SymbolValidator:
    def validate(self, password, user=None):
        if not re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', password):  # noqa
            raise ValidationError(
                _("This password must contain at least 1 symbol: " +
                  "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?"),  # noqa
                code='password_no_symbol')

    def validate_name(self, name):
        if re.findall('[()[\]{}|\\`~!@#$%^&*_\-+=;:\'",<>./?]', name):  # noqa
            raise ValidationError(
                _("The name contains special symbol"),
                code='name_with_symbol')

    def get_help_text(self):
        return _(
            "Your password must contain at least 1 symbol: " +
            "()[]{}|\`~!@#$%^&*_-+=;:'\",<>./?")  # noqa
