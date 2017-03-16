from .JSONResponse import JSONResponse
from match.serializers import UserSerializer,UserProfileSerializer

from django.conf.urls import include,url
from django.contrib.auth.models import Group,User
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import decorators,permissions,routers,status,viewsets
from rest_framework.routers import DefaultRouter

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ['admin']
    queryset = User.objects.select_related('profile').all()

    serializer_class = UserSerializer

    def list(self, request):
        if request.user and request.user.is_staff:
            return super(viewsets.ModelViewSet, self).list(request)
        else:
            return JSONResponse({"detail": "You need to be an admin to view this content."}, status=status.HTTP_403_FORBIDDEN)

    def create(self, request):
            userdata = dict(request.data)
            userdata.pop("profile", None)
            serializer = UserSerializer(data=userdata)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if 'profile' in serializer.validated_data:
                up_serializer = UserProfileSerializer(data=request.user.profile)
                up_serializer.is_valid(raise_exception=True)
                profile = User.objects.get(username=request.data.email)
                up_serializer.update(profile, request.user.profile)
                serializer = UserSerializer(User.objects.get(username=serializer.email))
                return JSONResponse(serializer.data, status=status.HTTP_201_CREATED)

            else:
                return JSONResponse(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, *args, **kwargs):
        serializer = UserSerializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JSONResponse(serializer.data)

    @decorators.detail_route()
    def me(self, request):
        serializer = UserSerializer(request.user)
        return JSONResponse(serializer.data)

    @decorators.detail_route(required_scopes=['write'])
    def partial_me(self, request, **kwargs):
        serializer =UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JSONResponse(serializer.data)

    # remove permissions for user creation.
    def get_permissions(self):
        if self.action == 'create':
            self.permission_classes = [permissions.AllowAny,]
        elif self.action in ['me', 'partial_me']:
            self.permission_classes = [permissions.IsAuthenticated]
        return super(self.__class__, self).get_permissions()

user_list = UserViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

user_me = UserViewSet.as_view({
    'get': 'me',
    'patch': 'partial_me'
})

user_detail = UserViewSet.as_view({
    'get': 'retrieve',
    'patch': 'patch',
    'delete': 'destroy'
})

urlpatterns = [
    url(r'^$', user_list, name='user-list'),
    url(r'^me/', user_me, name='user-me'),
    url(r'^(?P<pk>[0-9]+)', user_detail, name='user-detail')
]
