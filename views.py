from django.shortcuts import render_to_response
from forms import ContactForm
from django.template import RequestContext
from django.http import HttpResponseRedirect

def contact(request):
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():
			return HttpResponseRedirect('/thanks')
	else:
		form = ContactForm()


	return render_to_response('contact.html', {
		'form': form,
		}, context_instance=RequestContext(request))