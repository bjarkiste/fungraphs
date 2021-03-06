from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from population.models import Municipality, Population

# Create your views here.

def index(request):
    return plot(request)
    template = loader.get_template("heat/heatmap.html")
    context = RequestContext(request, {
        'mapsactive': True,
        'title': 'Choropleth',
        'subbanner' : True,
        'subbanner_data' : [
                ("By population", "/maps/pop", False),
                ("Population changes", "/maps/change", False),
                ],
        'css' : ["css/svgmap.css"],
        'js':["jquery-1.10.2.min.js", "d3.v2.min.js"]
        }, processors = [])
    return HttpResponse(template.render(context))

def preset(request, group):
    return plot(request, "group" + group)

def plot(request):
    groups = [300, 1000, 5000, 30000]
    def calc_group(n):
        for i,g in zip(range(len(groups)),groups):
            if n < g:
                return i
        return len(groups)

    raw = Population.objects.filter(municipality__mid__isnull=False).order_by('year')
    data = {}
    for obj in raw:
        if obj.year not in data:
            data[obj.year] = []
        data[obj.year].append(( obj.municipality.name, obj.municipality.mid, obj.val, calc_group(obj.val)))
    lis = []
    for key in data:
        lis.append((key, data[key]))
        lis[-1][1].sort(key=lambda x:x[1])
    lis.sort(key=lambda x:x[0])
    # if len raw .,
    template = loader.get_template("heat/heatmap.html")
    context = RequestContext(request, { 
        'mapsactive': True,
        'title': "Population choropleth",
        'subtitle' : '{} choropleth'.format('Population'),
        'choroplethdata' : lis,
        'groups': groups,
#        'subbanner' : True,
#        'subbanner_data' : [("By population", "/maps/", True)],
        'css' : ["css/svgmap.css"],
        'js':["jquery-1.10.2.min.js", "d3.v2.min.js"]
        }, processors = [])
    return HttpResponse(template.render(context))

