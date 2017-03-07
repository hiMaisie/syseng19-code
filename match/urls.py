from django.conf.urls import include,url
from match import views

urlpatterns = [
    url(r'^tags/?$', views.tag.tag_list, name="tag_list"),
    url(r'^users/', include(views.user))
]
