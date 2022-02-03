from zipfile import BadZipFile

from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from openpyxl import load_workbook

from .forms import UploadForm
from .validator.constants import ETABLISSEMENTS_FIELDS, ROLES_FIELDS
from .validator.row_models import EtabRows, RoleRows, SiretError
from .validator.search_api import check_siret


class TabException(Exception):
    pass


class InvalidHeaderException(Exception):
    pass


def load_xlsx(file):
    wb = load_workbook(filename=file)
    sheetnames = wb.sheetnames
    if len(sheetnames) != 2:
        raise TabException
    if sheetnames[0] != "etablissements":
        raise TabException
    if sheetnames[1] != "roles":
        raise TabException
    return wb


def validate_header(first_row, expected_header):
    """Validate first worksheet row matches `expected_header`"""

    header = [cell.value for cell in first_row]
    print(header, expected_header)
    if header != expected_header:
        raise InvalidHeaderException


class ValidateView(FormView):
    form_class = UploadForm
    template_name = "mass_validator/upload.html"
    success_url = reverse_lazy("result")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = []
        self.parse_error = False
        self.enough_rows_error = False
        self.siret_errors = []
        self.has_errors = False

    def check_sirets_exists(self, etab_rows):
        for row in etab_rows:
            if not check_siret(row.siret):
                self.siret_errors.append(
                    SiretError(siret=row.siret, row_number=row.index)
                )

    def parse(self, file):
        try:
            wb = load_xlsx(file)
        except (BadZipFile, KeyError, TabException):
            self.parse_error = True
            return

        ws_etablissements = wb.worksheets[0]

        ws_roles = wb.worksheets[1]
        etab_first_row = ws_etablissements[1][: len(ETABLISSEMENTS_FIELDS)]
        role_first_row = ws_roles[1][: len(ROLES_FIELDS)]

        try:
            validate_header(etab_first_row, ETABLISSEMENTS_FIELDS)
            validate_header(role_first_row, ROLES_FIELDS)
        except InvalidHeaderException:
            self.parse_error = True
            return

        etab_rows = EtabRows.from_worksheet(ws_etablissements)

        etab_rows.validate()

        if not etab_rows.has_enough_rows:
            self.enough_rows_error = True
            return

        role_rows = RoleRows.from_worksheet(ws_roles)

        role_rows.validate(etab_rows.sirets())

        if not etab_rows.is_valid:
            self.errors.extend(etab_rows.get_errors())
        if not role_rows.is_valid:
            self.errors.extend(role_rows.get_errors())

        # This validation can occur when both tabs are already validated
        if etab_rows.is_valid and role_rows.is_valid:
            etab_rows.validate_have_admin(role_rows.admin_sirets())
            if not etab_rows.is_valid:
                self.errors.extend(etab_rows.get_errors())

        # only performs api checks if everything else passes
        if not self.errors:
            self.check_sirets_exists(etab_rows)

    def form_valid(self, form):
        res = super().form_valid(form)

        file = self.request.FILES["file"]

        self.parse(file)

        self.has_errors = (
            self.errors
            or self.parse_error
            or self.siret_errors
            or self.enough_rows_error
        )
        if self.has_errors:
            return self.error_page()

        return res

    def error_page(self):
        return self.render_to_response(
            {
                "errors": self.errors,
                "parse_error": self.parse_error,
                "siret_errors": self.siret_errors,
                "has_errors": self.has_errors,
                "enough_rows_error": self.enough_rows_error,
            }
        )


class ResultView(TemplateView):
    template_name = "mass_validator/result.html"
