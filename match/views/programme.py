from .JSONResponse import JSONResponse
from match.models import Programme
from match.serializers import ProgrammeSerializer

from django.conf.urls import include,url
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import decorators,permissions,routers,status,viewsets
from rest_framework.routers import DefaultRouter

class ProgrammeViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ['read']
    queryset = Programme.objects.select_related('createdBy').all()

    serializer_class = ProgrammeSerializer

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'update', 'destroy']:
            self.permission_classes = [TokenHasScope, permissions.IsAdminUser]
            self.required_scopes = ['write', 'staff']
        return super(self.__class__, self).get_permissions()

    def get_object(self, request, **kwargs):
        serializer = ProgrammeSerializer(Programme.objects.get(programmeId=self.kwargs['programmeId']))
        return JSONResponse(serializer.data)

    def patch(self, request, **kwargs):
        p = Programme.objects.get(programmeId=self.kwargs['programmeId'])
        serializer = ProgrammeSerializer(p, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return JSONResponse(serializer.data)

programme_list = ProgrammeViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

programme_detail = ProgrammeViewSet.as_view({
    'get': 'get_object',
    'patch': 'patch',
    'delete': 'destroy'
})

urlpatterns = [
    url(r'^$', programme_list, name='programme-list'),
    url(r'^(?P<programmeId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', programme_detail, name='programme-detail')
]
