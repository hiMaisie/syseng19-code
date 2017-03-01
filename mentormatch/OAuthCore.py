from rest_framework.request import Request
from oauth2_provider import oauth2_backends


class OAuthLibCore(oauth2_backends.OAuthLibCore):
    """Backend for Django Rest Framework"""

    def extract_body(self, request):
        """
        DRF object keeps data in request.data whether django request
        inside POST
        """
        if isinstance(request, Request):
            try:
                return request.data.items()

                # complex json request (list?) is not easily serializable
            except (ValueError, AttributeError):
                return ""

        return super(OAuthLibCore, self).extract_body(request)
