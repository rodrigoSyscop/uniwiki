from django.conf.urls.defaults import patterns, include, url
from django.views.generic import DetailView, ListView, TemplateView
from wiki.models import News

urlpatterns = patterns('',
	url(r'^news/$',
		ListView.as_view(
			queryset=News.objects.order_by('-pub_date')[:10],
			context_object_name='latest_news_list',
			template_name='news/list.html'
			),
	),

	url(r'^news/(?P<pk>\d+)/?$',
		DetailView.as_view(
			model=News,
			template_name='news/detail.html'
		),
	),
)