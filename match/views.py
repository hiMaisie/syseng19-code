from django.contrib.auth.models import Group, User
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from match.models import *
from match.serializers import *
from oauth2_provider.ext.rest_framework import TokenHasReadWriteScope, TokenHasScope
from rest_framework import permissions,routers,viewsets
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

class JSONResponse(HttpResponse):

    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasReadWriteScope]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, TokenHasScope]
    required_scopes = ['groups']
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

@csrf_exempt
def tag_list(request):
    if request.method == 'GET':
        tags = Tag.objects.all()
        serializer = TagSerializer(tags, many=True)
        return JSONResponse(serializer.data)

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = TagSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JSONResponse(serializer.data, status=201)
        return JSONResponse(serializer.errors, status=400)
