# Borrowed from https://github.com/alsoicode/django-simple-math-captcha and slightly modified
# because current django version issues

from hashlib import sha1
from random import choice, randint

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import mark_safe
from django.utils.translation import gettext_lazy as _

MULTIPLY = "*"
ADD = "+"
SUBTRACT = "-"
CALCULATIONS = {
    MULTIPLY: lambda a, b: a * b,
    ADD: lambda a, b: a + b,
    SUBTRACT: lambda a, b: a - b,
}
OPERATORS = tuple(CALCULATIONS)


def hash_answer(value):
    answer = str(value)
    to_encode = (settings.SECRET_KEY + answer).encode("utf-8")
    return sha1(to_encode).hexdigest()


def get_operator():
    return choice(OPERATORS)


def get_numbers(start_int, end_int, operator):
    x = randint(start_int, end_int)
    y = randint(start_int, end_int)

    # avoid negative results for subtraction
    if y > x and operator == SUBTRACT:
        x, y = y, x

    return x, y


def calculate(x, y, operator):
    func = CALCULATIONS[operator]
    total = func(x, y)
    return total


class MathCaptchaWidget(forms.MultiWidget):
    template_name = "captcha/captcha.html"

    def __init__(
        self,
        start_int=1,
        end_int=10,
        question_tmpl=None,
        question_class=None,
        attrs=None,
    ):
        self.start_int, self.end_int = self.verify_numbers(start_int, end_int)
        self.question_class = question_class or "captcha-question"
        self.question_tmpl = "Combien font %(num1)i %(operator)s %(num2)i? "
        self.question_html = None
        widget_attrs = {"size": "5"}
        widget_attrs.update(attrs or {})
        widgets = (
            # this is the answer input field
            forms.TextInput(attrs=widget_attrs),
            # this is the hashed answer field to compare to
            forms.HiddenInput(),
        )
        super(MathCaptchaWidget, self).__init__(widgets, attrs)

    def get_context(self, *args, **kwargs):
        context = super(MathCaptchaWidget, self).get_context(*args, **kwargs)
        context["question_class"] = self.question_class
        context["question_html"] = self.question_html
        return context

    def decompress(self, value):
        return [None, None]

    def render(self, name, value, attrs=None, renderer=None):
        # hash answer and set as the hidden value of form
        hashed_answer = self.generate_captcha()
        value = ["", hashed_answer]

        return super(MathCaptchaWidget, self).render(name, value, attrs=attrs, renderer=renderer)

    def generate_captcha(self):
        # get operator for calculation
        operator = get_operator()

        # get integers for calculation
        x, y = get_numbers(self.start_int, self.end_int, operator)

        # set question to display in output
        self.set_question(x, y, operator)

        # preform the calculation
        total = calculate(x, y, operator)

        return hash_answer(total)

    def set_question(self, x, y, operator):
        # make multiplication operator more human-readable
        operator_for_label = "&times;" if operator == "*" else operator
        question = self.question_tmpl % {
            "num1": x,
            "operator": operator_for_label,
            "num2": y,
        }

        self.question_html = mark_safe(question)

    def verify_numbers(self, start_int, end_int):
        start_int, end_int = int(start_int), int(end_int)
        if start_int < 0 or end_int < 0:
            raise Warning("MathCaptchaWidget requires positive integers " "for start_int and end_int.")
        elif end_int < start_int:
            raise Warning("MathCaptchaWidget requires end_int be greater " "than start_int.")
        return start_int, end_int


class MathCaptchaField(forms.MultiValueField):
    default_error_messages = {
        "invalid": "Le calcul est faux",
        "invalid_number": "Entrez un nombre entier",
    }

    def __init__(self, *args, **kwargs):
        self._ensure_widget(kwargs)
        kwargs["required"] = True
        # we skip MultiValueField handling of fields and setup ourselves
        super(MathCaptchaField, self).__init__((), *args, **kwargs)
        self._setup_fields()

    def compress(self, data_list):
        """Compress takes the place of clean with MultiValueFields"""
        if data_list:
            answer = data_list[0]
            real_hashed_answer = data_list[1]
            hashed_answer = hash_answer(answer)
            if hashed_answer != real_hashed_answer:
                raise ValidationError(self.error_messages["invalid"])
        return None

    def _ensure_widget(self, kwargs):
        widget_params = self._extract_widget_params(kwargs)

        if "widget" not in kwargs or not kwargs["widget"]:
            kwargs["widget"] = MathCaptchaWidget(**widget_params)
        elif widget_params:
            msg = _("%(params)s must be omitted when widget is provided for %(name)s.")
            msg = msg % {
                "params": " and ".join(list(widget_params)),
                "name": self.__class__.__name__,
            }
            raise TypeError(msg)

    def _extract_widget_params(self, kwargs):
        params = {}
        for key in ("start_int", "end_int"):
            if key in kwargs:
                params[key] = kwargs.pop(key)
        return params

    def _setup_fields(self):
        error_messages = {"invalid": self.error_messages["invalid_number"]}
        # set fields
        fields = (
            forms.IntegerField(error_messages=error_messages, localize=self.localize),
            forms.CharField(),
        )
        for field in fields:
            field.required = False
        self.fields = fields
