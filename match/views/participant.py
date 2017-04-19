from .JSONResponse import JSONResponse
from match.models import Cohort,MentorshipScore,Participant
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
        if self.action in ['destroy']:
            self.permission_classes = [TokenHasScope, permissions.IsAdminUser]
            self.required_scopes = ['write']
        if self.action == 'setTopThree':
            self.required_scopes = ['write']
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
        try:
            p = Participant.objects.get(participantId=self.kwargs['participantId'])
            if not p.user.username == self.request.user.username:
                return JSONResponse({'detail': 'You do not have permission to see this participant\'s details'}, status=status.HTTP_403_FORBIDDEN)
            if p.isMentor:
                return JSONResponse({'detail': 'Only mentees can view their top three matches'}, status=status.HTTP_403_FORBIDDEN)
            if timezone.now() < p.cohort.closeDate:
                return JSONResponse({'detail': 'Matching has not yet begun'}, status=status.HTTP_403_FORBIDDEN)
            if timezone.now() > p.cohort.matchDate:
                return JSONResponse({'detail': 'Matching is finished, you can no longer view your top three'}, status=status.HTTP_403_FORBIDDEN)
            topThree = p.getTopThree()
            ps = ParticipantSerializer(topThree, many=True)
            return JSONResponse(ps.data, status=status.HTTP_200_OK)
        except Participant.DoesNotExist:
            return JSONResponse({'detail': 'Participant not found with that ID'}, status=status.HTTP_404_NOT_FOUND)

    @decorators.detail_route(methods=['post'], required_scopes=['read', 'write'])
    def setTopThree(self, request, **kwargs):
        try:
            participant = Participant.objects.get(participantId=self.kwargs['participantId'])
            if not participant.user.username == self.request.user.username:
                return JSONResponse({'detail': 'You do not have permission to modify this participant\'s details'}, status=status.HTTP_403_FORBIDDEN)
            if participant.isMentor:
                return JSONResponse({'detail': 'Only mentees can choose their top three matches'}, status=status.HTTP_403_FORBIDDEN)
            if timezone.now() < participant.cohort.closeDate:
                return JSONResponse({'detail': 'Matching has not yet begun, you cannot chose your top three matches'}, status=status.HTTP_403_FORBIDDEN)
            if timezone.now() > participant.cohort.matchDate:
                return JSONResponse({'detail': 'Matching is finished, you can no longer choose your top three matches'}, status=status.HTTP_403_FORBIDDEN)
            if participant.isTopThreeSelected:
                return JSONResponse({'detail': 'You have already selected your top three.'}, status=status.HTTP_403_FORBIDDEN)

            # get TopThree and ensure that user's selection is from the topThree.
            topThree = participant.getTopThree()
            choices = []
            try:
                choices = self.request.data.getlist('choices')
            except KeyError:
                return JSONResponse({'detail': 'You must include a list of the user\'s topThree choices. See the API documentation for more detail.'}, status=status.HTTP_400_BAD_REQUEST)
            if not len(choices) == len(topThree):
                return JSONResponse({'detail': 'You must choose all of the user\'s top three matches, ordered by user preference'}, status=status.HTTP_403_FORBIDDEN)
            for p in topThree:
                if not str(p.participantId) in choices:
                    return JSONResponse({'detail': 'You must choose all of the user\'s top three matches, ordered by user preference'}, status=status.HTTP_403_FORBIDDEN)
            
            participant.setTopThree(choices)
            return JSONResponse({'detail': 'Top Three successfully selected'}, status=status.HTTP_200_OK)
        except Participant.DoesNotExist:
            return JSONResponse({'detail': 'Participant not found with that ID'}, status=status.HTTP_404_NOT_FOUND)

participant_list = ParticipantViewSet.as_view({
    'get': 'list'
})

participant_detail = ParticipantViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

participant_top_three = ParticipantViewSet.as_view({
    'get': 'getTopThree',
    'post': 'setTopThree'
})

urlpatterns = [
    url(r'^$', participant_list, name='participant-list'),
    url(r'^(?P<participantId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', participant_detail, name='participant-detail'),
    url(r'^(?P<participantId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/topThree$', participant_top_three, name='participant-top-three'),
]
