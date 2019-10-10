from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView, RedirectView
from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'compareorgs.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^job_status/(?P<job_id>[0-9A-Za-z_\-]+)/$', 'compareorgs.views.job_status'),
	url(r'^download_status/(?P<job_id>[0-9A-Za-z_\-]+)/$', 'compareorgs.views.download_status'),
    url(r'^compare_orgs/(?P<job_id>[0-9A-Za-z_\-]+)/$', 'compareorgs.views.compare_orgs'),
    url(r'^compare_result/(?P<job_id>[0-9A-Za-z_\-]+)/$', 'compareorgs.views.compare_results'),
    url(r'^re-run-job/(?P<job_id>[0-9A-Za-z_\-]+)/$', 'compareorgs.views.rerunjob'),
    url(r'^check_file_status/(?P<job_id>[0-9A-Za-z_\-]+)/$', 'compareorgs.views.check_file_status'),
    url(r'^get_metadata/(?P<component_id>\d+)/$', 'compareorgs.views.get_metadata'),
    url(r'^get_diffhtml/(?P<component_id>\d+)/$', 'compareorgs.views.get_diffhtml'),
) + (static(settings.STATIC_URL, document_root=settings.STATIC_ROOT))

