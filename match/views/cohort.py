from .JSONResponse import JSONResponse
from match.models import Cohort,Participant
from match.serializers import CohortSerializer,ParticipantSerializer,UserSerializer

from django.conf.urls import include,url
from django.db.utils import IntegrityError
from django.http import Http404
import json
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import decorators,permissions,routers,status,viewsets
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import ValidationError

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

    @decorators.detail_route(methods=['post'], required_scopes=['read','write'])
    def register(self, request, **kwargs):
        c = Cohort.objects.get(cohortId=self.kwargs['cohortId'])
        s = ParticipantSerializer(data=request.data)
        if not s.is_valid():
            return JSONResponse({'detail': s.errors}, status=status.HTTP_400_BAD_REQUEST)
        try:
            s.save(user=request.user, cohort=c)
        except IntegrityError:
            return JSONResponse({'detail': 'You have already applied for this cohort.'}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return JSONResponse({'detail': e.args[0]}, status=status.HTTP_403_FORBIDDEN)
        return JSONResponse(s.data, status=status.HTTP_200_OK)
    
    @decorators.detail_route(methods=['get'], required_scopes=['read'])
    def get_registration(self, request, **kwargs):
        c = Cohort.objects.get(cohortId=self.kwargs['cohortId'])
        try:
            participant = Participant.objects.get(cohort=c, user=self.request.user)
        except Participant.DoesNotExist:
            return JSONResponse({'detail': 'User not signed up for this cohort'}, status=status.HTTP_404_NOT_FOUND)
        s = ParticipantSerializer(participant)
        return JSONResponse(s.data)

cohort_list = CohortViewSet.as_view({
    'get': 'list'
})

cohort_detail = CohortViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy'
})

cohort_register = CohortViewSet.as_view({
    'get': 'get_registration',
    'post': 'register'
})

urlpatterns = [
    url(r'^$', cohort_list, name='cohort-list'),
    url(r'^(?P<cohortId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/register$', cohort_register, name='cohort-register'),
    url(r'^(?P<cohortId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', cohort_detail, name='cohort-detail'),
]
