from django.core.urlresolvers import reverse

def nav_hook(context):
	url = reverse('view_supporting_institutions')
	return '<li><a href="{0}">Supporting Institutions</a></li>'.format(url)
