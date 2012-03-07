from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView

urlpatterns = patterns('wm.views',
	url(r'^$|^index/$', 'viewCheck'),
	url(r'^register/$', 'register'),
	url(r'^login/$', 'login'),
	url(r'^logout/$', 'logout'),
	url(r'^addcheck/$|^addcheck$', 'addCheck'),
	url(r'^editplan/(?P<wday>\d)/(?P<ptype>\d)/$', 'editPlan'),
	url(r'^plan/(?P<wday>\d)/(?P<ptype>\d)/$|plan/|plan$', 'plan'),
	url(r'^a_getcheck/$|^a_getcheck$', 'a_getCheck'),
	url(r'^a_namelist/$|^a_namelist$', 'a_namelist'),
	url(r'^viewcheck/$|^viewcheck$|^viewcheck/(?P<page>\d+)/', 'viewCheck'),
	url(r'^detail/(?P<cid>\d+)/$', 'detail'),
	url(r'^del/$', 'delete'),
	url(r'^ot/$', 'ot'),
	url(r'^getsalary/(?P<mode>\d)/$', 'getSalary'),
	url(r'^fallback/$', 'fallback'),
	url(r'^allsalary/(?P<page>\d+)/$|^allsalary/$', 'allSalary'),
	url(r'^sbymonth/(?P<year>\d{1,4})/(?P<month>\d{1,2})/$', 'sByMonth'),
	url(r'^delsalary/$', 'delSalary'),
	url(r'^download/$', 'download'),
	url(r'^test', 'test'),
	url(r'^.*$', 'viewCheck'),
)
