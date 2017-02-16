from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

# Ensure joinDate is earlier than today's date.
def validate_joinDate(value):
    if value > timezone.now():
        raise ValidationError(
            _('%(value)s is later than current date'),
            params={'value': value}
        )
