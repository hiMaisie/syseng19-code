from .JSONResponse import JSONResponse
from match.models import Cohort
from match.serializers import CohortSerializer,UserSerializer

from django.conf.urls import include,url
from django.http import Http404
import json
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import decorators,permissions,routers,status,viewsets
from rest_framework.routers import DefaultRouter

class CohortViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ['read']
    queryset = Cohort.objects.select_related('createdBy').all()

    serializer_class = CohortSerializer

    lookup_field = 'cohortId'

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'destroy']:
            self.permission_classes = [TokenHasScope, permissions.IsAdminUser]
            self.required_scopes = ['write', 'staff']
        return super(self.__class__, self).get_permissions()

    def partial_update(self, request, **kwargs):
        # Prevent non-owner from patching this object.
        c = Cohort.objects.get(cohortId=self.kwargs['cohortId'])
        if self.request.user == c.createdBy:
            return super(self.__class__, self).partial_update(request, **kwargs)
        else:
            return JSONResponse({'detail': 'You do not have permission to perform this action. (you do not own the resource)'}, status=status.HTTP_403_FORBIDDEN)

    def destroy(self, request, **kwargs):
        # Prevent non-owner from deleting this object.
        c = Cohort.objects.get(cohortId=self.kwargs['cohortId'])
        if self.request.user == c.createdBy:
            return super(self.__class__, self).destroy(request, **kwargs)
        else:
            return JSONResponse({'detail': 'You do not have permission to perform this action. (you do not own the resource)'}, status=status.HTTP_403_FORBIDDEN)

cohort_list = CohortViewSet.as_view({
    'get': 'list'
})

cohort_detail = CohortViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy'
})

urlpatterns = [
    url(r'^$', cohort_list, name='cohort-list'),
    url(r'^(?P<cohortId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', cohort_detail, name='cohort-detail'),
]
