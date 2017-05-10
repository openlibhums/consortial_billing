from django.http import HttpResponse

def index(request):
	return HttpResponse("<p>This is a dummy plugin. It does nothing.</p>")