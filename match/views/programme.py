from .JSONResponse import JSONResponse
from match.models import Programme
from match.serializers import ProgrammeSerializer

from django.conf.urls import include,url
from django.http import Http404
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import decorators,permissions,routers,status,viewsets
from rest_framework.routers import DefaultRouter

class ProgrammeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ['read']
    queryset = Programme.objects.select_related('createdBy').all()

    serializer_class = ProgrammeSerializer

    lookup_field = 'programmeId'

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'destroy']:
            self.permission_classes = [TokenHasScope, permissions.IsAdminUser]
            self.required_scopes = ['write', 'staff']
        return super(self.__class__, self).get_permissions()

    def create(self, request, **kwargs):
        # implicitly add createdBy attribute
        if not 'createdBy' in request.data:
            request.data['createdBy'] = request.user.pk
        return super(self.__class__, self).create(request, **kwargs)

    def partial_update(self, request, **kwargs):
        # Prevent non-owner from patching this object.
        p = Programme.objects.get(programmeId=self.kwargs['programmeId'])
        if self.request.user == p.createdBy:
            return super(self.__class__, self).partial_update(request, **kwargs)
        else:
            return JSONResponse({'detail': 'You do not have permission to perform this action. (you do not own the resource)'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, **kwargs):
        # Prevent non-owner from deleting this object.
        p = Programme.objects.get(programmeId=self.kwargs['programmeId'])
        if self.request.user == p.createdBy:
            return super(self.__class__, self).destroy(request, **kwargs)
        else:
            return JSONResponse({'detail': 'You do not have permission to perform this action. (you do not own the resource)'}, status=status.HTTP_403_FORBIDDEN)

programme_list = ProgrammeViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

programme_detail = ProgrammeViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    url(r'^$', programme_list, name='programme-list'),
    url(r'^(?P<programmeId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', programme_detail, name='programme-detail')
]
