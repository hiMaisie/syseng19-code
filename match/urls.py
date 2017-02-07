from django.conf.urls import url
from match import views

urlpatterns = [
    url(r'^tags/?$', views.tag_list)
]
