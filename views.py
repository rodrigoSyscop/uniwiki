from django.shortcuts import render_to_response
from forms import ContactForm
from django.template import RequestContext
from django.http import HttpResponseRedirect

def contact(request):
	if request.method == 'POST':
		form = ContactForm(request.POST)
		if form.is_valid():

			subject   = form.cleaned_data['subject']
			message   = form.cleaned_data['message']
			sender    = form.cleaned_data['sender']
			cc_myself = form.cleaned_data['cc_myself']

			recipients = ['contato@uniwiki.br']
			if cc_myself:
				recipients.append(sender)

			# as confs de e-mail no settings.py sao ficticias
			# por isso send_mail esta comentada
			# send_mail(subject, message, sender, recipients)

			return HttpResponseRedirect('/thanks')
	else:
		form = ContactForm()


	return render_to_response('contact.html', {
		'form': form,
		}, context_instance=RequestContext(request))