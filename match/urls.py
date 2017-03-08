from django.conf.urls import include,url
from match import views

urlpatterns = [
    url(r'^tags/?$', views.tag.tag_list, name="tag_list"),
    url(r'^user/', include(views.user.urlpatterns))
    # url(r'^user/', include(views.user.UserViewSet, namespace='users'))
]
