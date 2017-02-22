from django.conf.urls import include,url
from match import views

urlpatterns = [
    url(r'^tags/?$', views.tag_list, name="tag_list"),
    url(r'^', include(views.router.urls))
]
