from django.conf.urls import include,url
from match import views

urlpatterns = [
    url(r'^cohort/', include(views.cohort.urlpatterns)),
    url(r'^programme/', include(views.programme.urlpatterns)),
    url(r'^tags/?$', views.tag.tag_list, name="tag_list"),
    url(r'^user/', include(views.user.urlpatterns))
]
