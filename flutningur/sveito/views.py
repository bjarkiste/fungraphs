from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models import Sum, F, FloatField, Avg
from population.models import Municipality, Changes, Population, GenderPop, Regions, SpendingPerCapita
from flutningur.utils import IS_sort
from flutningur.constants import get_bad_mid, get_good_mid

# Create your views here.
regioncolor = ['#8dd3c7','#ffffb3','#bebada','#fb8072','#80b1d3','#fdb462','#b3de69','#fccde5']


def index(request):
    template = loader.get_template("sveito/index.html")
    raw = Municipality.objects.filter(mid__isnull=False).order_by('region__name','name')
    data = {}
    for obj in raw:
        if obj.region not in data:
            data[obj.region] = []
        data[obj.region].append((obj.name, obj.mid))
    region = []
    for d in data:
        data[d].sort(key=lambda x: IS_sort()(x[0]))
        region.append((d.name, regioncolor[d.id-1], data[d], d.id))
    region.sort(key=lambda x: x[3])
    arst = [region[0:4],region[4:]]


    context = RequestContext(request, { 
            'title' : 'Municipalities',
            'sveitoactive': True,
            'css' : ["css/svgmap.css"],
            'columns' : arst,
            'regioncolor': regioncolor,
            'js':["jquery-1.10.2.min.js", "d3.v2.min.js"]
        }, processors = [])
    return HttpResponse(template.render(context))


def sveito(request, mid):
    try:
        mun = Municipality.objects.get(mid=int(mid))
    except Municipality.DoesNotExist:
        raise Http404('Municipality does not exist')

    #gets change table for a specific municipality
    #recursion ho!
    def getChanges(mun, fromYear=2015):
        changes = [] 
        for i in Changes.objects.filter(new=mun):
            if i.year > fromYear: continue
            #If it is not 100% then there was a split
            if i.percent != 100:
                total = False
                for split in Changes.objects.filter(old=i.old,year=i.year).exclude(new=i.new):
                    changes.append((split.old.name,split.new.name,split.year))
                if not total: changes.append((i.old.name,i.old.name,i.year))

            changes.append((i.old.name,i.new.name,i.year))
            if i.old.name != i.new.name: changes += getChanges(i.old,i.year)

        #Handle the cases where something splits from our muni
        changes = sorted(changes, key=lambda x:x[2])[::-1]


        #This might be a bit dirty but the set conversion fixes it
        splits = []
        for i in changes:
            for split in Changes.objects.filter(old=Municipality.objects.get(name=i[0])):
                splits.append((split.old.name,split.new.name,split.year)) 

        return changes+splits

    #Double loops are in P
    def niceChanges(mun):
        changes = getChanges(mun)
        changes.sort(key=lambda x:x[1])
        dic = {}    
        for change in changes:
            f, t, y = change
            if y not in dic: dic[y] = [[],[]]
            dic[y][0].append(f)
            dic[y][1].append(t)

        changes = []
        for y in dic:
            changes.append((y, ", ".join(list(set(dic[y][0]))), ", ".join(list(set(dic[y][1])))))
        changes.sort(key=lambda x:x[0])
        return changes[::-1]

    #    changes = getChanges(mun)
    #    years = set(map(lambda x:x[2], changes))
    #    return [[y for y in changes if y[2]==x] for x in years] 

    changes = niceChanges(mun)
    #Year is permanently hardcoded
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
                lis.append((d['year'], 100 * res[i]['ratio'] / d['total']))
        return lis
    good = get_good_mid()
    bad = get_bad_mid()
    lineplot=[]
    tmp = GenderPop.objects.filter(year__gte=2000)
    lineplot.append((namefix('Alls'),ratio(tmp.filter(municipality__name='Alls'))))
    lineplot.append((namefix('good'),ratio(tmp.filter(municipality__mid__in=good))))
    lineplot.append((namefix('bad'),ratio(tmp.filter(municipality__mid__in=bad))))
    lineplot.append((mun,ratio(tmp.filter(municipality__mid=int(mid)))))
    lineplot.append((reg,ratio(tmp.filter(municipality__region_id=reg_ind))))

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
    'lineplot' : {"values": lineplot, "height":500, "opacity":0.6, "linewidth":"4px",
        "valformat": "0.2f",
        "y" : {
            "name":"Percent of males",
            "format": "d",
            "force": "49,51,50,",
            }
        },
    'munipop' : munipop,
    'changes' : changes
    },processors=[])
    return HttpResponse(template.render(context))
