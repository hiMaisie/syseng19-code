from .JSONResponse import JSONResponse
from match.models import Cohort,Programme
from match.serializers import CohortSerializer,ProgrammeSerializer,UserSerializer

from django.conf.urls import include,url
from django.http import Http404
import json
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
        if self.action in ['create', 'partial_update', 'cohort_create']:
            self.permission_classes = [TokenHasScope, permissions.IsAdminUser]
            self.required_scopes = ['write', 'staff']
        if self.action == "destroy":
            self.permission_classes = [TokenHasScope, permissions.IsAdminUser]
            self.required_scopes = ['write', 'admin']
        return super(self.__class__, self).get_permissions()

    def perform_create(self, serializer):
        if not "createdBy" in serializer.validated_data:
            serializer.save(createdBy=self.request.user)
        serializer.save()

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

    # Cohort methods
    def cohort_list(self, request, **kwargs):
        programme = Programme.objects.get(programmeId=kwargs['programmeId'])
        if not programme:
            return JSONResponse({'detail': 'Programme not found'}, status=status.HTTP_404_NOT_FOUND)
        try:
            cohorts = Cohort.objects.filter(programme=programme.programmeId)
            serializer = CohortSerializer(data=cohorts, many=True)
            serializer.is_valid()
            return JSONResponse(serializer.data, status=status.HTTP_200_OK)
        except Cohort.DoesNotExist:
            return JSONResponse(None, status=status.HTTP_204_NO_CONTENT)

    @decorators.detail_route(methods=['get'], required_scopes=['read'])
    def cohort_active(self, request, **kwargs):
        programme = Programme.objects.get(programmeId=kwargs['programmeId'])
        if not programme:
            return JSONResponse({'detail': 'Programme not found'}, status=status.HTTP_404_NOT_FOUND)
        cohort = programme.activeCohort
        if cohort:
            serializer = CohortSerializer(cohort)
            return JSONResponse(serializer.data, status=status.HTTP_200_OK)
        else:
            return JSONResponse({}, status=status.HTTP_404_NOT_FOUND)


    @decorators.detail_route(methods=['post'], required_scopes=['write staff'])
    def cohort_create(self, request, **kwargs):
        programme = Programme.objects.get(programmeId=kwargs['programmeId'])
        if not programme:
            return JSONResponse({'detail': 'Programme not found'}, status=status.HTTP_404_NOT_FOUND)
        # Add defaultCohortSize if no cohortSize present
        input_data = request.data
        if not "cohortSize" in input_data:
            input_data["cohortSize"] = programme.defaultCohortSize
        serializer = CohortSerializer(data=input_data)
        if not serializer.is_valid():
            return JSONResponse({'detail': 'Your request data is invalid.', 'errors':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        if not "createdBy" in serializer.validated_data:
            serializer.save(createdBy=self.request.user, programme=programme)
        else:
            serializer.save(programme=programme)
        return JSONResponse(serializer.data, status=status.HTTP_201_CREATED)

programme_list = ProgrammeViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

programme_detail = ProgrammeViewSet.as_view({
    'get': 'retrieve',
    'patch': 'partial_update',
    'delete': 'destroy'
})

programme_active_cohort = ProgrammeViewSet.as_view({
    'get': 'cohort_active',
})

programme_cohort = ProgrammeViewSet.as_view({
    'post': 'cohort_create',
    'get': 'cohort_list',
})

urlpatterns = [
    url(r'^$', programme_list, name='programme-list'),
    url(r'^(?P<programmeId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', programme_detail, name='programme-detail'),
    url(r'^(?P<programmeId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/cohorts/$', programme_cohort, name='programme-cohort-list'),
    url(r'^(?P<programmeId>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/cohorts/active$', programme_active_cohort, name='programme-active-cohort'),
]
