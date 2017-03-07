from . import JSONResponse
from match.serializers import UserSerializer,GroupSerializer

from django.conf.urls import include,url
from django.contrib.auth.models import Group,User
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import permissions,routers,viewsets

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope, permissions.IsAdminUser]
    required_scopes = ['admin']
    queryset = User.objects.select_related('profile').all()

    serializer_class = UserSerializer

router = routers.DefaultRouter()
router.register(r'', UserViewSet, base_name='user')

urlpatterns = router.urls
