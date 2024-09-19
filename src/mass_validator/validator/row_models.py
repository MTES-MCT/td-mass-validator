import re
from itertools import chain

import attr
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator

from .constants import (
    COLLECTOR_TYPES,
    COMPANY_TYPES,
    ERROR_STR,
    ETABLISSEMENTS_CREATE_FIELDS,
    ETABLISSEMENTS_UPDATE_FIELDS,
    MAX_ETAB_CREATE_COL,
    MAX_ETAB_UPDATE_COL,
    MAX_ROLE_COL,
    MIN_ETAB_ROW,
    MIN_ROLE_ROW,
    ROLES_FIELDS,
    USER_ROLES,
    VALID_STR,
    WASTE_PROCESSOR_TYPES,
    WASTE_VEHICLE_TYPES,
)
from .helpers import dict_read, format_csv_row, quote

company_types = ",".join(COMPANY_TYPES)
collector_types = ",".join(COLLECTOR_TYPES)
waste_processor_types = ",".join(WASTE_PROCESSOR_TYPES)
waste_vehicles_types = ",".join(WASTE_VEHICLE_TYPES)
user_roles = ",".join(USER_ROLES)

phone_re = re.compile(r"^(0[1-9])(?:[ _.-]?(\d{2})){4}$")

ETABLISSEMENTS_TAB = "Établissements"
ROLES_TAB = "Rôles"

ERROR_FIELD = "field"
ERROR_SIRET_MISSING_FROM_ETAB = "siret_missing_from_etab"
ERROR_SIRET_HAS_NO_ADMIN = "siret_has_no_admin"
ERROR_DUPLICATE_ROLE = "duplicate_role"

ERROR_TYPES = [
    ERROR_FIELD,
    ERROR_SIRET_MISSING_FROM_ETAB,
    ERROR_SIRET_HAS_NO_ADMIN,
    ERROR_DUPLICATE_ROLE,
]


class BaseRow:
    @property
    def is_valid(self):
        if not self.validated:
            raise Exception("Not validated yet")
        return not self.errors

    def siret_is_valid(self):
        return len(str(self.siret)) == 14

    @classmethod
    def from_dict(cls, idx, the_dict):
        if all([not v for v in the_dict.values()]):  # skip empty rows
            return

        return cls(**the_dict, index=idx)


class BaseRows:
    def __iter__(self):
        yield from self.rows

    def append(self, row):
        if not self.header:
            self.header = row
        else:
            self.rows.append(row)

    def get_errors(self):
        errors = [row.errors for row in self.rows]
        return chain.from_iterable(errors)


@attr.s()
class RowError:
    row_number = attr.ib()
    field_name = attr.ib()
    field_value = attr.ib()
    error_type = attr.ib(default=ERROR_FIELD)

    tab = attr.ib(default="")

    @error_type.validator
    def _check_error_type(self, attribute, value):
        return value in ERROR_TYPES

    @property
    def displayable_value(self):
        if self.field_name == "companyTypes" and isinstance(self.field_value, list):
            return ",".join(self.field_value)
        return self.field_value

    def as_str(self):
        return f"{self.field_name.capitalize()} error on row n°{self.row_number} value={self.field_value}"

    def verbose_error_field(self):
        error_config = {
            "siret": "Format de siret incorrect, un siret est composé de 14 chiffres",
            "companyTypes": f"Le champ companyTypes accepte uniquement les valeurs {company_types} séparées par des virgules",
            "collectorTypes": f"Le champ collectorTypes accepte uniquement les valeurs {collector_types} séparées par des virgules. Le champ companyTypes doit contenir COLLECTOR.",
            "wasteProcessorTypes": f"Le champ collectorTypes accepte uniquement les valeurs {waste_processor_types} séparées par des virgules.Le champ companyTypes doit contenir WASTE_PROCESSOR.",
            "wasteVehiclesTypes": f"Le champ wasteVehiclesTypes accepte uniquement les valeurs {waste_vehicles_types} séparées par des virgules. Le champ companyTypes doit contenir WASTE_VEHICLES.",
            "role": f"Le champ role accepte uniquement les valeurs {user_roles}",
            "email": "Valeur incorrecte, les adresses emails doivent être correctement formées",
            "contactEmail": "Valeur incorrecte, les adresses emails doivent être correctement formées",
        }

        return error_config.get(self.field_name)

    def verbose_error_missing_siret(self):
        return "Siret absent de l'onglet établissements"

    def verbose_error_siret_has_no_admin(self):
        return "Le siret n'a pas d'ADMIN identifié dans l'onglet rôles"

    def message_error_duplicate_role(self):
        return "Le rôle est dupliqué, un email ne peut être associé à un siret qu'un seule fois"

    @property
    def verbose(self):
        if self.error_type == ERROR_SIRET_MISSING_FROM_ETAB:
            return self.verbose_error_missing_siret()
        if self.error_type == ERROR_SIRET_HAS_NO_ADMIN:
            return self.verbose_error_siret_has_no_admin()
        if self.error_type == ERROR_DUPLICATE_ROLE:
            return self.message_error_duplicate_role()
        return self.verbose_error_field()


@attr.s()
class SiretError:
    siret = attr.ib()
    row_number = attr.ib()

    @property
    def verbose(self):
        return "Ce siret est non diffusible"


@attr.s()
class EtabCreateRow(BaseRow):
    index = attr.ib()
    siret = attr.ib(default="")
    gerepId = attr.ib(default="")
    companyTypes = attr.ib(default=attr.Factory(list))
    collectorTypes = attr.ib(default=attr.Factory(list))
    wasteProcessorTypes = attr.ib(default=attr.Factory(list))
    wasteVehiclesTypes = attr.ib(default=attr.Factory(list))
    givenName = attr.ib(default="")
    contactEmail = attr.ib(default="")
    contactPhone = attr.ib(default="")
    contact = attr.ib(default="")
    website = attr.ib(default="")

    errors = attr.ib(default=attr.Factory(list))
    validated = attr.ib(default=False)
    tab_name = ETABLISSEMENTS_TAB

    def as_str(self):
        return f"{self.siret} {self.givenName} {self.contactEmail}"

    def as_list(self):
        return [
            str(self.index),
            self.siret,
            self.gerepId,
            ",".join(self.companyTypes),
            ",".join(self.collectorTypes),
            ",".join(self.wasteProcessorTypes),
            ",".join(self.wasteVehiclesTypes),
            self.givenName,
            self.contactEmail,
            self.contactPhone,
            self.contact,
            self.website,
            ERROR_STR if not self.is_valid else VALID_STR,
        ]

    def as_csv(self):
        quoted = [
            quote(self.siret),
            quote(self.gerepId),
            ",".join(self.companyTypes),
            ",".join(self.collectorTypes),
            ",".join(self.wasteProcessorTypes),
            ",".join(self.wasteVehiclesTypes),
            quote(self.givenName),
            quote(self.contactEmail),
            quote(self.contactPhone),
            quote(self.contact),
            quote(self.website),
        ]
        return format_csv_row(quoted)

    def company_types_are_valid(self):
        if not self.companyTypes:
            return False
        return all([c_type in COMPANY_TYPES for c_type in self.companyTypes])

    def collector_types_are_valid(self):
        if not self.collectorTypes:
            return True
        if "COLLECTOR" not in self.companyTypes:
            return False
        return all([c_type in COLLECTOR_TYPES for c_type in self.collectorTypes])

    def waste_processor_types_are_valid(self):
        if not self.wasteProcessorTypes:
            return True
        if "WASTEPROCESSOR" not in self.companyTypes:
            return False

        return all([c_type in WASTE_PROCESSOR_TYPES for c_type in self.wasteProcessorTypes])

    def waste_vehicle_types_are_valid(self):
        if not self.wasteVehiclesTypes:
            return True
        if "WASTE_VEHICLES" not in self.companyTypes:
            return False
        return all([c_type in WASTE_VEHICLE_TYPES for c_type in self.wasteVehiclesTypes])

    def phone_number_is_valid(self):
        if not self.contactPhone:
            return True
        return phone_re.match(self.contactPhone) is not None

    def email_is_valid(self):
        if not self.contactEmail:
            return True
        try:
            EmailValidator()(
                self.contactEmail,
            )
            return True
        except ValidationError:
            return False

    def validate(self):
        if not self.siret_is_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="siret",
                    field_value=self.siret,
                    tab=self.tab_name,
                )
            )
        if not self.company_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="companyTypes",
                    field_value=self.companyTypes,
                    tab=self.tab_name,
                )
            )
        if not self.collector_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="collectorTypes",
                    field_value=self.collectorTypes,
                    tab=self.tab_name,
                )
            )
        if not self.waste_processor_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="wasteProcessorTypes",
                    field_value=self.wasteProcessorTypes,
                    tab=self.tab_name,
                )
            )
        if not self.waste_vehicle_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="wasteVehiclesTypes",
                    field_value=self.wasteVehiclesTypes,
                    tab=self.tab_name,
                )
            )
        if not self.phone_number_is_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="contactPhone",
                    field_value=self.contactPhone,
                    tab=self.tab_name,
                )
            )
        if not self.email_is_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="contactEmail",
                    field_value=self.contactEmail,
                    tab=self.tab_name,
                )
            )
        self.validated = True

    def validate_has_admin(self, admin_sirets):
        if self.siret not in admin_sirets:
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="siret",
                    field_value=self.siret,
                    tab=self.tab_name,
                    error_type=ERROR_SIRET_HAS_NO_ADMIN,
                )
            )
            self.validated = True


@attr.s()
class EtabCreateRows(BaseRows):
    header = attr.ib(default="")
    rows = attr.ib(default=attr.Factory(list))
    is_valid = attr.ib(default=False)
    has_enough_rows = attr.ib(default=True)
    has_too_many_rows = attr.ib(default=False)
    siret_errors = attr.ib(default=attr.Factory(list))
    verbose_errors = attr.ib(default=attr.Factory(list))

    def append(self, row):
        if not self.header:
            self.header = row
        else:
            self.rows.append(row)

    def sirets(self):
        return list(set([item.siret for item in self if item.siret]))

    def validate(self):
        self.is_valid = True
        if len(self.rows) < 10:
            self.has_enough_rows = False
            return
        if len(self.rows) > 500:
            self.has_too_many_rows = True
            return
        for row in self:
            row.validate()
            if not row.is_valid:
                self.is_valid = False

    def validate_have_admin(self, admin_sirets):
        for row in self:
            row.validate_has_admin(admin_sirets)
            if not row.is_valid:
                self.is_valid = False

    def as_csv(self):
        ret = []
        ret.append(format_csv_row([quote(fn) for fn in ETABLISSEMENTS_CREATE_FIELDS]))
        for row in self:
            ret.append(row.as_csv())
        return ret

    @classmethod
    def from_worksheet(cls, worksheet):
        etab_rows = []
        idx = 1
        for row in worksheet.iter_rows(min_row=MIN_ETAB_ROW, max_col=MAX_ETAB_CREATE_COL):
            data = dict_read(row, ETABLISSEMENTS_CREATE_FIELDS)

            if idx != 1:
                etab_row = EtabCreateRow.from_dict(idx, data)

                if etab_row:
                    etab_rows.append(etab_row)
            idx += 1

        return cls(rows=etab_rows)


@attr.s()
class RoleRow(BaseRow):
    index = attr.ib()
    siret = attr.ib()
    email = attr.ib()
    role = attr.ib()
    errors = attr.ib(default=attr.Factory(list))
    validated = attr.ib(default=False)
    tab_name = ROLES_TAB

    def as_str(self):
        return f"{self.siret} {self.role} {self.email}"

    def as_list(self):
        return [
            str(self.index),
            self.siret,
            self.email,
            self.role,
            ERROR_STR if not self.is_valid else VALID_STR,
        ]

    def as_csv(self):
        quoted = [
            quote(self.siret),
            quote(self.email),
            quote(self.role),
        ]
        return format_csv_row(quoted)

    def role_is_valid(self):
        return self.role in ["MEMBER", "ADMIN"]

    def siret_belongs_to(self, etab_sirets):
        return self.siret in etab_sirets

    def email_is_valid(self):
        if not self.email:
            return False

        try:
            EmailValidator()(
                self.email,
            )
            return True
        except ValidationError:
            return False

    def validate(self, etab_sirets):
        if not self.role_is_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="role",
                    field_value=self.role,
                    tab=self.tab_name,
                )
            )
        if not self.siret_is_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="siret",
                    field_value=self.siret,
                    tab=self.tab_name,
                )
            )
        if not self.siret_belongs_to(etab_sirets):
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="siret",
                    field_value=self.siret,
                    tab=ROLES_TAB,
                    error_type=ERROR_SIRET_MISSING_FROM_ETAB,
                )
            )
        if not self.email_is_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="email",
                    field_value=self.email,
                    tab=self.tab_name,
                )
            )
        self.validated = True

    def mark_as_duplicate(self):
        self.errors.append(
            RowError(
                row_number=self.index,
                field_name="email",
                field_value=self.email,
                tab=self.tab_name,
                error_type=ERROR_DUPLICATE_ROLE,
            )
        )


@attr.s()
class RoleRows(BaseRows):
    header = attr.ib(default="")
    rows = attr.ib(default=attr.Factory(list))
    is_valid = attr.ib(default=False)
    verbose_errors = attr.ib(default=attr.Factory(list))

    def admin_sirets(self):
        return list(set([row.siret for row in self if row.siret and row.role == "ADMIN"]))

    def as_csv(self):
        ret = []
        ret.append(format_csv_row([quote(fn) for fn in ROLES_FIELDS]))
        for row in self:
            ret.append(row.as_csv())
        return ret

    def validate(self, etab_sirets):
        self.is_valid = True
        for row in self:
            row.validate(etab_sirets)
            if not row.is_valid:
                self.is_valid = False

        # Check for duplicates
        pairs = [f"{row.siret}_{row.email}" for row in self]
        seen = set()
        duplicates_idx = []
        for idx, pair in enumerate(pairs):
            if pair in seen:
                duplicates_idx.append(idx)
                self.rows[idx].mark_as_duplicate()

            if pair not in seen:
                seen.add(pair)

        if duplicates_idx:
            self.is_valid = False

    @classmethod
    def from_worksheet(cls, worksheet):
        role_rows = []
        idx = 1
        for row in worksheet.iter_rows(min_row=MIN_ROLE_ROW, max_col=MAX_ROLE_COL):
            data = dict_read(row, ROLES_FIELDS)
            if idx != 1:
                role_row = RoleRow.from_dict(idx, data)

                if role_row:
                    role_rows.append(role_row)
            idx += 1
        return cls(rows=role_rows)


@attr.s()
class EtabUpdateRow(BaseRow):
    index = attr.ib()
    siret = attr.ib(default="")

    companyTypes = attr.ib(default=attr.Factory(list))
    collectorTypes = attr.ib(default=attr.Factory(list))
    wasteProcessorTypes = attr.ib(default=attr.Factory(list))
    wasteVehiclesTypes = attr.ib(default=attr.Factory(list))

    errors = attr.ib(default=attr.Factory(list))
    validated = attr.ib(default=False)
    tab_name = ETABLISSEMENTS_TAB

    def as_str(self):
        return f"{self.siret}"

    def as_list(self):
        return [
            str(self.index),
            self.siret,
            ",".join(self.companyTypes),
            ",".join(self.collectorTypes),
            ",".join(self.wasteProcessorTypes),
            ",".join(self.wasteVehiclesTypes),
            ERROR_STR if not self.is_valid else VALID_STR,
        ]

    def as_csv(self):
        quoted = [
            quote(self.siret),
            ",".join(self.companyTypes),
            ",".join(self.collectorTypes),
            ",".join(self.wasteProcessorTypes),
            ",".join(self.wasteVehiclesTypes),
        ]
        return format_csv_row(quoted)

    def as_json(self):
        the_dict = attr.asdict(self)

        def process_field(k):
            if k == "siret":
                return "orgId"
            return k

        def process_value(value):
            if value is None:
                return []
            return value

        res = {
            process_field(field_name): process_value(value)
            for field_name, value in the_dict.items()
            if field_name in ETABLISSEMENTS_UPDATE_FIELDS
        }
        return res

    def company_types_are_valid(self):
        if not self.companyTypes:
            return False
        return all([c_type in COMPANY_TYPES for c_type in self.companyTypes])

    def collector_types_are_valid(self):
        if not self.collectorTypes:
            return True
        if "COLLECTOR" not in self.companyTypes:
            return False
        matches = [c_type in COLLECTOR_TYPES for c_type in self.collectorTypes]
        return all(matches) and len(matches)

    def waste_processor_types_are_valid(self):
        if not self.wasteProcessorTypes:
            return True
        if "WASTEPROCESSOR" not in self.companyTypes:
            return False
        matches = [c_type in WASTE_PROCESSOR_TYPES for c_type in self.wasteProcessorTypes]
        return all(matches) and len(matches)

    def waste_vehicle_types_are_valid(self):
        if not self.wasteVehiclesTypes:
            return True
        if "WASTE_VEHICLES" not in self.companyTypes:
            return False
        matches = [c_type in WASTE_VEHICLE_TYPES for c_type in self.wasteVehiclesTypes]
        return all(matches) and len(matches)

    def validate(self):
        if not self.siret_is_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="siret",
                    field_value=self.siret,
                    tab=self.tab_name,
                )
            )
        if not self.company_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="companyTypes",
                    field_value=self.companyTypes,
                    tab=self.tab_name,
                )
            )
        if not self.collector_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="collectorTypes",
                    field_value=self.collectorTypes,
                    tab=self.tab_name,
                )
            )
        if not self.waste_processor_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="wasteProcessorTypes",
                    field_value=self.wasteProcessorTypes,
                    tab=self.tab_name,
                )
            )
        if not self.waste_vehicle_types_are_valid():
            self.errors.append(
                RowError(
                    row_number=self.index,
                    field_name="wasteVehiclesTypes",
                    field_value=self.wasteVehiclesTypes,
                    tab=self.tab_name,
                )
            )
        # if not self.phone_number_is_valid():
        #     self.errors.append(
        #         RowError(
        #             row_number=self.index,
        #             field_name="contactPhone",
        #             field_value=self.contactPhone,
        #             tab=self.tab_name,
        #         )
        #     )
        # if not self.email_is_valid():
        #     self.errors.append(
        #         RowError(
        #             row_number=self.index,
        #             field_name="contactEmail",
        #             field_value=self.contactEmail,
        #             tab=self.tab_name,
        #         )
        #     )
        self.validated = True


@attr.s()
class EtabUpdateRows(BaseRows):
    header = attr.ib(default="")
    rows = attr.ib(default=attr.Factory(list))
    is_valid = attr.ib(default=False)
    has_enough_rows = attr.ib(default=True)
    has_too_many_rows = attr.ib(default=False)
    siret_errors = attr.ib(default=attr.Factory(list))
    verbose_errors = attr.ib(default=attr.Factory(list))

    def append(self, row):
        if not self.header:
            self.header = row
        else:
            self.rows.append(row)

    def sirets(self):
        return list(set([item.siret for item in self if item.siret]))

    def validate(self):
        self.is_valid = True
        if len(self.rows) < 3:
            self.has_enough_rows = False
            return
        if len(self.rows) > 500:
            self.has_too_many_rows = True
            return
        for row in self:
            row.validate()
            if not row.is_valid:
                self.is_valid = False

    def as_csv(self):
        ret = []
        ret.append(format_csv_row([quote(fn) for fn in ETABLISSEMENTS_UPDATE_FIELDS]))
        for row in self:
            ret.append(row.as_csv())
        return ret

    def as_json(self):
        ret = []
        for row in self:
            ret.append(row.as_json())
        return ret

    @classmethod
    def from_worksheet(cls, worksheet):
        etab_rows = []
        idx = 1
        for row in worksheet.iter_rows(min_row=MIN_ETAB_ROW, max_col=MAX_ETAB_UPDATE_COL):
            data = dict_read(row, ETABLISSEMENTS_UPDATE_FIELDS)

            if idx != 1:
                etab_row = EtabUpdateRow.from_dict(idx, data)

                if etab_row:
                    etab_rows.append(etab_row)
            idx += 1

        return cls(rows=etab_rows)
