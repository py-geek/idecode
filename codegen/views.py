from .forms import SnippetForm
from .models import Snippet
import requests

from django.shortcuts import render, redirect, render_to_response
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import RequestContext, loader
from django.template.response import TemplateResponse
from django.core.urlresolvers import reverse

COMPILE_URL = 'https://api.hackerearth.com/v3/code/compile/'
RUN_URL = 'https://api.hackerearth.com/v3/code/run/'

CLIENT_SECRET = 'de88e83b32f8ac80fa060182170efc867355b051'
DOWNLOAD_PREFIX = 'https://code.hackerearth.com/download/'

def simple(request):
    if request.method == 'POST':
        form = SnippetForm(request.POST)
        if form.is_valid():
            snippet = Snippet()
            snippet.text = form.cleaned_data['text']
            snippet.lang = form.cleaned_data['lang']
            snippet.file_name = form.cleaned_data['file_name']
            snippet.save()
            snippet.write_key = generate_key(snippet.code_id)
            snippet.save()
            return custom_redirect('update_code', snippet.code_id, key = snippet.write_key)
            # form = SnippetForm(initial={'text': snippet.text, 'lang':snippet.lang})
            # return render(request, "snippets.html", {
            #     "form": form, "code":snippet,
            # })
        else:
            form = SnippetForm(initial={'file_name':'Untitled File'})
    else:
        form = SnippetForm(initial={'file_name':'Untitled File'})
    return render(request, "snippets.html", {
        "form": form,
    })

def custom_redirect(url_name, *args, **kwargs):
    from django.core.urlresolvers import reverse 
    import urllib
    url = reverse(url_name, args = args)
    params = urllib.urlencode(kwargs)
    return HttpResponseRedirect(url + "?%s" % params)

def generate_key(code_id):
  from hashlib import md5
  from time import localtime
  return "%s" % (md5(str(localtime()) + str(code_id)).hexdigest())

def compile_n_run( source, lang):
    data = {
            'client_secret': CLIENT_SECRET,
            'async': 0,
            'source': source,
            'lang': 'PYTHON',
            'time_limit': 5,
            'memory_limit': 262144,
        }
    r = requests.post(RUN_URL, data=data)
    return r.json()

def update_code(request, code_id):
    from django.core.exceptions import ObjectDoesNotExist
    context = RequestContext(request)
    print code_id
    try:
        code = Snippet.objects.get(pk=code_id)

    except ObjectDoesNotExist:
        return HttpResponseRedirect('/')

    write_key = request.GET.get('key', False)

    code_output = compile_n_run(code.text, code.lang)

    if write_key == code.write_key:
        read_only = False
        code.download_url = DOWNLOAD_PREFIX + str(code_output['code_id'])
        code.run_count += 1
        code.save()

    else:
        read_only = True

    form = SnippetForm(initial={'text': code.text, 'file_name':code.file_name})
    print code.text
    context_list = {
            'form':form,
            'code': code,
            'code_output' : code_output,
            'read_only' : read_only,
            }
    return render_to_response('codepage.html',context_list,context)