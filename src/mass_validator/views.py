from zipfile import BadZipFile

from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from openpyxl import load_workbook

from .forms import UploadForm
from .validator.row_models import EtabRows, RoleRows, SiretError
from .validator.search_api import check_siret


class TabException(Exception):
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


class ValidateView(FormView):
    form_class = UploadForm
    template_name = "mass_validator/upload.html"
    success_url = reverse_lazy("result")
    errors = []
    parse_error = False
    siret_errors = []
    has_errors = False

    def check_sirets_exists(self, sirets):
        for siret in sirets:
            if not check_siret(siret):
                # message = (f"Le siret {siret} n'a pas été trouvé dans la base sirene. Il s'agit d'un établissemnent "
                #            f"non diffusible, veuillez nous transmettre un certificat d'inscription au répertoire "
                #            f"Sirene ou une attestation de situation au répertoire Sirene")

                self.siret_errors.append(SiretError(siret))

    def parse(self, file):
        try:
            wb = load_xlsx(file)
        except (BadZipFile, KeyError, TabException):
            self.parse_error = True
            return

        ws_etablissements = wb.worksheets[0]
        ws_roles = wb.worksheets[1]

        etab_rows = EtabRows.from_worksheet(ws_etablissements)

        etab_rows.validate()

        role_rows = RoleRows.from_worksheet(ws_roles)

        role_rows.validate(etab_rows.sirets())

        if not etab_rows.is_valid:
            self.errors.extend(etab_rows.get_errors())
        if not role_rows.is_valid:
            self.errors.extend(role_rows.get_errors())

        if not self.errors:
            sirets = etab_rows.sirets()
            self.check_sirets_exists(sirets)

    def form_valid(self, form):
        res = super().form_valid(form)

        file = self.request.FILES["file"]

        self.parse(file)
        self.has_errors = self.errors or self.parse_error or self.siret_errors
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
            }
        )


class ResultView(TemplateView):
    template_name = "mass_validator/result.html"
