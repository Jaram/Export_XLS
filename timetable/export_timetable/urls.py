from django.conf.urls import patterns, include, url

from .views import ExportXLS

urlpatterns = patterns('',
    url(r'^$', ExportXLS.as_view()),
)
