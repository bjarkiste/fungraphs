from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from population.models import Municipality, Population
from flutningur.utils import IS_sort
from django.shortcuts import redirect
from flutningur.constants import get_bad_mid, get_good_mid

# Create your views here.

def index(request):
    return redirect('/plot/log')

def scale(request, scale='linear'):
    args = ",".join([str(m.mid) for m in Municipality.objects.filter(mid__isnull=False)])
    return plot(request, args, scale=scale)

def preset(request, group, scale='linear'):
    if int(group) == 0:
        lis = [str(r) for r in get_good_mid()]
    elif int(group) == 9:
        lis = [str(r) for r in get_bad_mid()]
    else:
        lis = [str(m.mid) for m in Municipality.objects.filter(region__id=int(group))]
    args = ",".join(lis)
    return plot(request, args, scale=scale)

def plot(request, args, scale='linear'):
    islog = scale == 'log'
    mun_lis = [int(s) for s in args.split(',')]
    raw = Population.objects.filter(municipality__mid__in=mun_lis).order_by('municipality__name', 'year')
    data = {}
    for line in raw:
        name = line.municipality.name
        if not name in data:
            data[name] = []
        data[name].append((line.year,line.val))
    lis = []
    for key in data:
        lis.append((key, data[key]))
    lis.sort(key=lambda x: IS_sort()(x[0]))
    lineplot_d = {
            "values": lis,
            "log": islog,
            "height":500,
            "hidelegend":True,
            "linewidth":"2px",
            "y" : {"name":"Population", "format": "" }
        }

    template = loader.get_template("plot/index.html")
    context = RequestContext(request, {
                'title' : 'Population {}line plot'.format("logarithmic " if islog else ""),
                'plotactive': True,
                'lineplot' : lineplot_d,
                'css' : [ "lib/nvd3/build/nv.d3.min.css" ],
                'js': ["lib/d3/d3.min.js", "lib/nvd3/build/nv.d3.min.js" ],
            },
            processors = [])
    return HttpResponse(template.render(context))
