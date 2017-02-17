from django.core.exceptions import ValidationError
from datetime import date
from django.utils.translation import ugettext_lazy as _

# Ensure joinDate is earlier than today's date.
def validate_joinDate(value):
    if value > date.today():
        raise ValidationError(
            _('%(value)s is later than current date'),
            params={'value': value}
        )
