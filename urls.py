from django.conf.urls.defaults import patterns, include, url
from django.views.generic import TemplateView
from django.conf import settings


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'uniwiki.views.home', name='home'),
    # url(r'^uniwiki/', include('uniwiki.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
    	'document_root': settings.MEDIA_ROOT,
    	}),
    url(r'^wiki/', include('wiki.urls')),
    url(r'^about$',
    	TemplateView.as_view(
    		template_name='about.html'
    		),
    	),
    url(r'^contact$', 'views.contact'),
    url(r'^$',
    	TemplateView.as_view(
    		template_name='index.html'
    		),
    	),
)
