from .JSONResponse import JSONResponse
from match.models import Cohort,Participant
from match.serializers import CohortSerializer,ParticipantSerializer,UserSerializer

from django.conf.urls import include,url
from django.db.utils import IntegrityError
from django.http import Http404
from django.utils import timezone
import json
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import decorators,permissions,routers,status,viewsets
from rest_framework.routers import DefaultRouter
from rest_framework.serializers import ValidationError

class ParticipantViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ['read']
    #queryset = Cohort.objects.select_related('createdBy').all()
    queryset = Participant.objects.all()

    serializer_class = ParticipantSerializer

    lookup_field = 'participantId'

    def get_permissions(self):
        if self.action in ['create', 'partial_update', 'destroy']:
            self.permission_classes = [TokenHasScope, permissions.IsAdminUser]
            self.required_scopes = ['write', 'staff']
        return super(self.__class__, self).get_permissions()

    def list(self, request, **kwargs):
        self.queryset = Participant.objects.filter(user=self.request.user)
        return super(self.__class__, self).list(request, **kwargs)

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
    def getTopThree(self, request, **kwargs):
        p = None
        try:
            p = Participants.objects.get(participantId=self.kwargs['participantId'])
            if not p.user.username == self.request.user.username:
                return JSONResponse({'detail': 'You do not have permission to see this participant\'s details'}, status=status.HTTP_403_FORBIDDEN)
            if p.isMentor:
                return JSONResponse({'detail': 'Only mentees can view their top three matches'}, status=status.HTTP_403_FORBIDDEN)
            if timezone.now() < p.cohort.closeDate:
                return JSONResponse({'detail': 'Matching has not yet begun'}, status=status.HTTP_403_FORBIDDEN)
            topThree = p.getTopThree()

        except Participant.DoesNotExist:
            return JSONResponse({'detail': 'Participant not found with that ID'}, status=status.HTTP_404_NOT_FOUND)

participant_list = ParticipantViewSet.as_view({
    'get': 'list'
})

participant_detail = ParticipantViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

urlpatterns = [
    url(r'^$', participant_list, name='participant-list'),
    url(r'^(?P<participantId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', participant_detail, name='participant-detail'),
]
