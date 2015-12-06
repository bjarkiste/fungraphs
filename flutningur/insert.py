#!/usr/bin/env python3
import csv
import os.path
from django.db import IntegrityError
from population.models import Municipality, Changes, Population

BRPATH = '../data/breytingar.txt'
PCPATH = '../data/skiptingar.csv'
DPATH = '../data'

def getMun(name):
	try:
		mun = Municipality.objects.get(name=name)
	except Municipality.DoesNotExist:
		mun = Municipality(name=name)
		mun.save()
	return mun

def getPercent():
	dic = {}
	with open(PCPATH) as f:
		for i in f:
			i = i.strip().split(',')
			dic[','.join(i[0:2])] = int(i[2])
	return dic


def addChanges():
	#Add the cnages to a database
	pdic = getPercent()
	#Create a list of changes
	s = []
	with open(BRPATH) as f:
		for i in f:
			if i == 'Fyrir,Eftir,Ártal\n': continue
			i = i.split(',')
			i[-1] = int(i[-1].strip())
			s.append(i)

	for i in s:
		old = i[0]
		oldMun = getMun(old)
		y = i[-1]
		new = i[1:-1]
		if len(new) > 1:
			for j in new:
				if old == j: continue
				try:
					per = pdic[','.join([old,j])]
				except KeyError:
					per = 50
					print('Need percent for {}: {}, {}'.format(old,j,y))
				newMun = getMun(j)
				change = Changes(old=oldMun,new=newMun,percent=per,year=y)
				change.save()
		else:
			new = new[0]
			if old == new: print('{} goes into only itself'.format(old))
			newMun = getMun(new)
			newMun.save()
			change = Changes(old=oldMun,new=newMun,percent=100,year=y)
			change.save()
			

def addPopulation():
	#1900 to 1990, every 10 years
	with open(os.path.join(DPATH, '1901-1990.csv')) as f:
		reader = csv.reader(f, delimiter=';')
		for i in reader:
			mun = getMun(i[0])
			data = i[1:]
			for y, val in enumerate(data):
				if val == '.' or val == '-': val = 0
				try:
					pop = Population(municipality=mun,year=1900+y*10,val=val)
					pop.save()
				except IntegrityError:
					print('Integrity error {}'.format(i[0]))


	#1991 to 2004 every year
	with open(os.path.join(DPATH, '1990-2004.csv')) as f:
		reader = csv.reader(f, delimiter=';')
		for i in reader:
			mun = getMun(i[0])
			data = i[1:]
			for y, val in enumerate(data):
				if val == '.' or val == '-': val = 0
				try:
					pop = Population(municipality=mun,year=1991+y,val=val)
					pop.save()
				except IntegrityError:
					print('Integrity error {}'.format(i[0]))


	#2005 to 2014 every year
	with open(os.path.join(DPATH, '2004-2014.csv')) as f:
		reader = csv.reader(f, delimiter=';')
		for i in reader:
			mun = getMun(i[0])
			data = i[1:]
			for y, val in enumerate(data):
				if val == '.' or val == '-': val = 0
				try:
					pop = Population(municipality=mun,year=2005+y,val=val)
					pop.save()
				except IntegrityError:
					print('Integrity error {}'.format(i[0]))


if __name__ == '__main__':
	import django
	django.setup()
	addChanges()
	addPopulation()