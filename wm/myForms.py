#-*- coding: UTF-8-*-
from django import forms
from wm.models import User

#class regForm(forms.Form):
#	stuNum = forms.CharField(max_length=8, label="学号")
#	name = forms.CharField(max_length=20, label="姓名")
#	password = forms.CharField(max_length=20, label="密码", widget=forms.PasswordInput)
#	pAgain = forms.CharField(max_length=20, label="再次输入密码", widget=forms.PasswordInput)
#	nickname = forms.CharField(max_length=20, label="昵称")

class regForm(forms.Form):
	stuNum = forms.CharField(max_length=8, label="学号")
	name = forms.CharField(max_length=20, label="姓名")
	nickname = forms.CharField(max_length=20, label="ECNC用户名")

class loginForm(forms.Form):
	stuNum = forms.CharField(max_length=8, label="学号")
	password = forms.CharField(max_length=20, label="密码", widget=forms.PasswordInput)

class nameForm(forms.Form):
	name = forms.CharField(max_length=20, label="姓名")

class checkForm(forms.Form):
	typeChoice = ((0,"上午"),(1,"中午"),(2,"下午"),(3,"晚上前台"),(4,"晚上小黑屋"))
	checkDate = forms.DateField(label="值班日期", widget=forms.DateInput)
	ptype = forms.ChoiceField(label="值班时段", choices=typeChoice)

class uCheckForm(forms.Form):
	name = forms.CharField(max_length=20, label="姓名")
	status = forms.ChoiceField(label="状态", choices=((0,"正常"),(1,"请假")))
	periodTime = forms.FloatField(label="值班时间")
	cDate = forms.DateField(widget=forms.HiddenInput)
	ptype = forms.IntegerField(widget=forms.HiddenInput)

class ticketForm(forms.Form):
	ticketNum = forms.CharField(max_length=7, label="Ticket单号")
	checkNum = forms.IntegerField(widget=forms.HiddenInput)
	reason = forms.CharField(max_length=300, label="故障原因")
	way = forms.CharField(max_length=300, label="处理方法")

class uTicketForm(forms.Form):
	name = forms.CharField(max_length=20, label="姓名")
	ticketNum = forms.CharField(max_length=7, widget=forms.HiddenInput)

class otForm(forms.Form):
	name = forms.CharField(max_length=20, label="姓名")
	dtInput = forms.DateTimeInput(format="%Y-%m-%d %H:%M:%S")
	otTime = forms.DateTimeField(label="加班时间", widget=dtInput)
	hours = forms.FloatField(label="加班时长")
	detail = forms.CharField(max_length=300, label="加班事由")

class salarySingleForm(forms.Form):
	name = forms.CharField(max_length=20, label="姓名")
	year = forms.IntegerField(label="年份")
	month = forms.IntegerField(label="月份")
	startDate = forms.DateField(label="开始日期")
	endDate = forms.DateField(label="结束日期")

class salaryAllForm(forms.Form):
	year = forms.IntegerField(label="年份")
	month = forms.IntegerField(label="月份")
	startDate = forms.DateField(label="开始日期")
	endDate = forms.DateField(label="结束日期")

class fileForm(forms.Form):
	file = forms.FileField()

class setHourForm(forms.Form):
	am = forms.FloatField(label="上午")
	noon = forms.FloatField(label='中午')
	pm = forms.FloatField(label='下午')
	nightDesk = forms.FloatField(label='晚上前台')
	darkHouse = forms.FloatField(label='小黑屋')
	wam = forms.FloatField(label='周末上午')
	wnoon = forms.FloatField(label='周末中午')
	wpm = forms.FloatField(label='周末下午')

class specialOtForm(forms.Form):
	otChoice = ((0,"负责人"),(1,"内务组"))
	year = forms.IntegerField(label="年份")
	month = forms.IntegerField(label="月份")
	hours = forms.FloatField(label="加班时长")
	ottype = forms.ChoiceField(label="加班类型", choices=otChoice)
