from django.db import models

# Create your models here.
class User(models.Model):
	stuNum = models.CharField(max_length=8, primary_key=True)
	name = models.CharField(max_length=20)
	password = models.CharField(max_length=32, null=True)
	nickname = models.CharField(max_length=20, null=True)
	role = models.CharField(max_length=20, null=True)
	salt = models.CharField(max_length=6,null=True)
	erase = models.IntegerField()

class Check(models.Model):
	checkDate = models.DateField()
	periodType = models.IntegerField()
	option = models.CharField(max_length=300)
	handler = models.ForeignKey('User')
	erase = models.IntegerField()

class UserCheck(models.Model):
	FK_user = models.ForeignKey('User')
	FK_check = models.ForeignKey('Check')
	timePeriod = models.FloatField()

class Ticket(models.Model):
	ticketNum = models.CharField(max_length=7, primary_key=True)
	FK_check = models.ForeignKey('Check')
	reason = models.CharField(max_length=300, null=True)
	way = models.CharField(max_length=300, null=True)

class UserTicket(models.Model):
	FK_user = models.ForeignKey('User')
	FK_ticket = models.ForeignKey('Ticket')

class Ot(models.Model):
	FK_user = models.ForeignKey('User')
	hours = models.FloatField()
	otTime = models.DateTimeField()
	detail = models.CharField(max_length=300)
	erase = models.IntegerField()

class Leave(models.Model):
	FK_user = models.ForeignKey('User')
	FK_check = models.ForeignKey('Check')
	sub = models.CharField(max_length=20, null=True)

class Absence(models.Model):
	FK_user = models.ForeignKey('User')
	FK_check = models.ForeignKey('Check')

class WorkPlan(models.Model):
	FK_user = models.ForeignKey('User')
	weekDay = models.IntegerField()
	periodType = models.IntegerField()

class Salary(models.Model):
	FK_user = models.ForeignKey('User')
	year = models.IntegerField()
	month = models.IntegerField()
	startDate = models.DateField()
	endDate = models.DateField()
	dayTime = models.FloatField()
	nightTime = models.FloatField()
	ticket = models.IntegerField()
	ot = models.IntegerField()
	fullWork = models.IntegerField()
	charger = models.IntegerField()
	leave = models.IntegerField()
	absence = models.IntegerField()
	total = models.FloatField()
	erase = models.IntegerField()

class pHour(models.Model):
	ptype = models.IntegerField()
	hour = models.FloatField()
	option = models.CharField(max_length=200)
