from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models import Sum, F, FloatField, Avg
from population.models import Municipality, Population, GenderPop, Regions, SpendingPerCapita

# Create your views here.

def index(request):
    template = loader.get_template("sveito/index.html")
    raw = Municipality.objects.filter(mid__isnull=False).order_by('region__name','name')
    data = {}
    for obj in raw:
        if obj.region.name not in data:
            data[obj.region.name] = []
        data[obj.region.name].append((obj.name, obj.mid))
    context = RequestContext(request, { 
            'title' : 'Municipalities',
            'sveitoactive': True,
            'css' : ["mystyle.css"],
            'regions' : data,
            'regioncolor': True,
            'js':["jquery-1.10.2.min.js", "d3.v2.min.js"]
        }, processors = [])
    return HttpResponse(template.render(context))


def sveito(request, mid):
    try:
        mun = Municipality.objects.get(mid=int(mid))
    except Municipality.DoesNotExist:
        raise Http404('Municipality does not exist')

    #Year is temporarily hardcoded
    year = 2014

    munipop = Population.objects.get(municipality=mun,year=year).val

    mun = mun.name
    #Create the data for population pyramids
    gpop = []
    gpop_obj = GenderPop.objects.filter(municipality__mid=int(mid),year=year)
    for i in gpop_obj:
        gpop.append([i.ageclass,i.valm,i.valf,i.year])

    #Add the data from total iceland
    gpop_all = []
    gpop_obj = GenderPop.objects.filter(municipality__name="Alls",year=year)
    for i in gpop_obj:
        gpop_all.append([i.ageclass,i.valm,i.valf,i.year])


    #Add the data for spending
    reg_ind = -1
    for i in Regions.objects.all():
        if i.low <= int(mid) <= i.high:
            reg = i.name
            reg_ind = i
            break

    names = ['Alls','good','bad',mun,reg]
    indnames = [(i,i) for i in names] 
    spending = []
    toPlot = [SpendingPerCapita.objects.get(name=i) for i in names]
 
    field_names = toPlot[0]._meta.get_all_field_names()

    verbose_name = {
        'culture' : 'culture',
        'social' : 'social services',
        'sports' : 'sports and youth activities'
    }

    def namefix(name):
        if name == 'Alls': return 'Iceland'
        if name == 'good': return 'Persistent growth'
        if name == 'bad' : return 'Persistent depopulation'
        return name

    for field in field_names:
        if field == 'name' or field == 'id' or field == 'income' or field == 'health': continue
        s = [(verbose_name[field],'Sveito')]
        for model in toPlot:
            s.append((getattr(model,field)/1000,namefix(model.name)))
        spending.append(s)

    #print(GenderPop.objects.filter(municipality__mid=int(mid)).values('year').annotate(Sum('valm')))
    def ratio(obj):
        lis = []
        res = obj.values('year').annotate(ratio=Sum(F('valm')))
        for i,d in zip(range(len(res)), obj.values('year').annotate(total=Sum(F('valm')+F('valf')))):
            if res[i]['year'] != d['year']:
                print('Error: year are not the same')
            if d['total']:
                lis.append((d['year'], res[i]['ratio'] / d['total']))
        return lis

    good = [1000,1400,8200,1300,1604,2000]
    bad = [4200,7617,4604,6100,4911,4607,6706,5609,7000,8509,4902,6250,7613]
    lineplot=[]
    lineplot.append((namefix('Alls'),ratio(GenderPop.objects.filter(municipality__name='Alls'))))
    lineplot.append((mun,ratio(GenderPop.objects.filter(municipality__mid=int(mid)))))
    lineplot.append((reg,ratio(GenderPop.objects.filter(municipality__region_id=reg_ind))))
    lineplot.append((namefix('good'),ratio(GenderPop.objects.filter(municipality__mid__in=good))))
    lineplot.append((namefix('bad'),ratio(GenderPop.objects.filter(municipality__mid__in=bad))))
    print(lineplot)

    #sorting for consistency 
    spending.sort(key= lambda x:x[1])
    spending = spending[::-1]
 
    template = loader.get_template("sveito/sveito.html")
    context = RequestContext(request, {
    'title' : mun,
    'sveitoactive' : True,
    'js' : ['lib/d3/d3.min.js', 'lib/nvd3/build/nv.d3.min.js'],
    'css' : ['lib/nvd3/build/nv.d3.min.css'],
    'region': reg, 
    'gpop' : gpop,
    'allgpop' : gpop_all,
    'spending' : spending,
    'lineplot' : lineplot,
    'munipop' : munipop
    },processors=[])
    return HttpResponse(template.render(context))
