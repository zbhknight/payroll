#-*- coding=utf-8 -*8
from wm.models import *
from wm.myForms import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from md5 import md5
from django.utils import simplejson
import datetime, time, csv
from django.db import connections, transaction

days = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
types = ['上午', '中午', '下午', '晚上前台', '晚上小黑屋', '周末上午', '周末下午']

# Create your views here.
def getDayType(wday, ptype):
	days = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
	types = ['上午', '中午', '下午', '晚上前台', '晚上小黑屋', '周末上午', '周末下午']
	result = days[int(wday)-1] + ' ' + types[int(ptype)-1]
	return result

def getDay(wday):
	days = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
	return days[int(wday)-1]

def getType(ptype):
	types = ['上午', '中午', '下午', '晚上前台', '晚上小黑屋', '周末上午', '周末下午']
	return types[int(ptype)-1]

def checkLogin(request):
	user = request.session.get('user')
	if user != None:
		return True
	else:
		return False

def login(request, error=''):
	if checkLogin(request):
		return HttpResponseRedirect("/wm/index")
	elif request.method == "POST":
		lF = loginForm(request.POST)
		if lF.is_valid():
			data = lF.cleaned_data
			try:
				u = User.objects.get(stuNum=data['stuNum'], erase=0)
			except User.DoesNotExist:
				errorList = "用户名错误"
				lF = loginForm()
				return render_to_response("wm/login.html", {"form": lF,"error":errorList,}, context_instance=RequestContext(request))
			if u.password == md5(md5(data['password']).hexdigest()+u.salt).hexdigest():
				request.session['user'] = u
				request.session.set_expiry(0)
				return HttpResponseRedirect("/wm/index/")
			else:
				errorList = "密码错误"
				return render_to_response("wm/login.html", {"form": lF,"error":errorList,}, context_instance=RequestContext(request))
		else:
			return HttpResponseRedirect("/wm/login")
	else:
		lF = loginForm()
		return render_to_response("wm/login.html", {"form": lF,"error":error,}, context_instance=RequestContext(request))

def logout(request):
	try:
		del request.session['user']
		return HttpResponse(u"你已安全退出")
	except KeyError:
		return HttpResponse(u"你尚未登录，无须退出")

def index(request):
	if checkLogin(request):
		p = request.session['user'].name
		r = request.session['user'].role
		leftTime = request.session.get_expiry_age()
		return render_to_response("wm/index.html", {'p': p,'r':r,'l':leftTime})
	else:
		return HttpResponseRedirect("/wm/login/")

#旧的注册页面，用和ECNC同步取代
#def register(request):
#	if checkLogin(request):
#		return HttpResponseRedirect('/wm/index')
#	elif request.method == 'POST':
#		rF = regForm(request.POST)
#		if rF.is_valid():
#			data = rF.cleaned_data
#			newUser = User(name=data['name'], stuNum=data['stuNum'], password=hash(data['password']), nickname=data['nickname'], role="normal", erase=0)
#			newUser.save()
#			return HttpResponseRedirect("/wm/login")
#		else:
#			return HttpResponseRedirect("/wm/register")
#	else:
#		rF = regForm()
#		return render_to_response('wm/register.html', {'form': rF,}, context_instance=RequestContext(request))

def register(request):
	if checkLogin(request):
		return HttpResponseRedirect("/wm/index/")
	elif request.method == "POST":
		rF = regForm(request.POST)
		if rF.is_valid():
			data = rF.cleaned_data
			uList = User.objects.filter(stuNum=data['stuNum'], name=data['name'])
			if len(uList) == 1:
				if uList[0].nickname is None:
					cursor = connections['syn_db'].cursor()
					cursor.execute('select password, salt from cdb_uc_members where username=%s', [data['nickname']])
					row = cursor.fetchall()
					row = list(row)
					if len(row) == 1:
						uList.update(password=row[0][0], salt=row[0][1], nickname=data['nickname'])
						back = u'与ECNC同步成功，请用学号和ECNC密码登录'
						return render_to_response("wm/fallback.html", {'back':back,'new':"new"})
					else:
						error = u'ECNC用户名错误'
				else:
					error = u'你的账户已同步'
			else:
				error = u"用户名和学号错误"
		else:
			error = u'输入信息有误'
		rF = regForm()
		return render_to_response('wm/register.html', {'form': rF,'error':error}, context_instance=RequestContext(request))
	else:
		rF = regForm()
		return render_to_response('wm/register.html', {'form': rF,}, context_instance=RequestContext(request))

def addCheck(request):
	if checkLogin(request) and (request.session['user'].role == 'mm' or request.session['user'].role == 'black'):
		cF = checkForm()
		return render_to_response("wm/check.html", {'checkForm':cF})
	else:
		return HttpResponseRedirect("/wm/index")

def editPlan(request, wday, ptype):
	if checkLogin(request) and request.session['user'].role == 'black':
		try:
			wday = int(wday)
			ptype = int(ptype)
		except:
			return HttpResponseRedirect("/wm/plan/")
		plist = WorkPlan.objects.raw('select * from wm_workplan, wm_user where weekDay=%s and periodType=%s and FK_user_id=stuNum', [wday, ptype])
		nameList = []
		for p in plist:
			nameList.append(p.name)
		if len(nameList) < 2:
			count = 1
		else:
			count = len(nameList)

		data = {
			'form-TOTAL_FORMS': str(count),
			'form-INITIAL_FORMS': u'0',
			'form-MAX_NUM_FORMS': u'',
		}
		keysList = []
		for i in range(len(nameList)):
			keysList.append('form-'+str(i)+'-name')
		data.update(zip(keysList, nameList))

		nameFormset = formset_factory(nameForm, extra=13)
		nFs = nameFormset(data)
		dayType = getDayType(wday,ptype)
		paramDict = {"formset":nFs,"count":count,"dayType":dayType,'one':wday,'two':ptype}
		if nFs.is_valid():
			return render_to_response("wm/editplan.html", paramDict, context_instance=RequestContext(request))
		else:
			return HttpResponse(nFs.errors)
	else:
		return HttpResponseRedirect("/wm/index")

def plan(request, wday=0, ptype=0):
	if checkLogin(request):
		if request.method == "POST" and request.session['user'].role == 'black':
			nameFormset = formset_factory(nameForm)
			nFs = nameFormset(request.POST)
			if nFs.is_valid():
				setData = nFs.cleaned_data
				nameList = [ nf['name'].strip() for nf in setData if len(nf) > 0 ]
				nameList = set(nameList)

				pList = WorkPlan.objects.filter(weekDay=wday, periodType=ptype)
				cmpList = []
				for p in pList:
					cmpList.append(p.FK_user.name)
				cmpList = set(cmpList)

				toDel = list(cmpList.difference(nameList))
				toDel2 = User.objects.filter(name__in=toDel, erase=0)
				toAdd = list(nameList.difference(cmpList))

				WorkPlan.objects.filter(weekDay=wday, periodType=ptype, FK_user__in=toDel2).delete()
				uList = User.objects.filter(name__in=toAdd, erase=0)
				for u in uList:
					newPlan = WorkPlan.objects.create(weekDay=wday, periodType=ptype,FK_user=u)
					newPlan.save()

				return HttpResponseRedirect("/wm/plan/%s/%s/" % (wday,ptype))
				
			else:
				return HttpResponseRedirect("/wm/plan")
		else:
			nums = [ 0 for i in range(7) ]
			allPlan = [ [] for i in range(35) ]
			for i in range(1,8,1):
				for j in range(1,6,1):
					if j == 1:
						pList = WorkPlan.objects.filter(weekDay=i, periodType__in=[1,6])
					elif j == 3:
						pList = WorkPlan.objects.filter(weekDay=i, periodType__in=[3,7])
					else:
						pList = WorkPlan.objects.filter(weekDay=i, periodType=j)
					for p in pList:
						allPlan[(j-1)*7+i-1].append(p.FK_user.name)

			index = [i for i in range(35)]
			allDict = dict(zip(index, allPlan))

			return render_to_response("wm/plan.html", {"types":types, "days":days, "allDict":allDict})
	else:
		return HttpResponseRedirect("/wm/login/")

def a_namelist(request):
	result = {'success':"False"}
	if request.method == "POST" and checkLogin(request):
		if request.POST.has_key('date') and request.POST.has_key('ptype'):
			checkDate = request.POST['date']
			ptype = int(request.POST['ptype']) + 1
			checkDate = checkDate.split('/')
			try:
				for i in range(len(checkDate)):
					checkDate[i] = int(checkDate[i])
			except:
				result['status'] = u'时间为空'
				json = simplejson.dumps(result)
				return HttpResponse(json, mimetype='application/json')

			wday = datetime.date(checkDate[2],checkDate[0],checkDate[1]).weekday() + 1
			if datetime.date(checkDate[2],checkDate[0],checkDate[1]) > datetime.date.today():
				result['status'] = u'请不要提前签到'
			else:
				pList = WorkPlan.objects.filter(weekDay=wday, periodType=ptype)
				nameList = [ p.FK_user.name for p in pList ]
				index = [ i for i in range(len(nameList)) ]
				nameDict = dict(zip(index, nameList))
				result['success'] = "True"
				result['namelist'] = nameList
				result['num'] = len(nameList)
				result['wday'] = wday
				result.update(nameDict)
		else:
			result['status'] = u'时间为空'
	elif request.method == "GET":
		result['success'] = True
		result['date'] = request.POST['date']
	json = simplejson.dumps(result)
	return HttpResponse(json, mimetype='application/json')

def test(request):
	pass

def a_getCheck(request):
	result = {'success':False}
	if checkLogin(request) and request.session['user'].role in ['mm','black'] and request.method == "POST":
		data = request.POST
		try:
			userNum = int(data['userNum'])
			ticketNum = int(data['ticketNum'])
		except:
			result['status'] = u"提交表单数据错误"
			json = simplejson.dumps(result)
			return HttpResponse(json, mimetype='application/json')

		#初始化数据
		cDate = data['cDate-0'].split('/')
		#cDate = cDate[2] + '-' + cDate[0] + '-' + cDate[1]
		#cDate = datetime.date(cDate[])
		try:
			for i in range(len(cDate)):
				cDate[i] = int(cDate[i])
			ptype = int(data['ptype-0']) + 1
			cDate = datetime.date(cDate[2], cDate[0], cDate[1])
		except:
			result['status'] = u"提交日期或工作类型错误"
			json = simplejson.dumps(result)
			return HttpResponse(json, mimetype='application/json')

		option = request.session['user'].name + u"创建于" + str(time.ctime())
		checkList = Check.objects.filter(checkDate=cDate, periodType=ptype, erase=0)
		if len(checkList) == 0:
			newCheck = Check(checkDate=cDate,periodType=ptype,option=option, handler=request.session['user'], erase=0)

			#初始化各种数据
			nameList = []
			timeDict = {}
			statusDict = {}
			subDict = {}
			try:
				for i in range(userNum):
					if data["name-"+str(i)] != '':
						nameList.append(data["name-"+str(i)])
						timeDict[data["name-"+str(i)]] = float(data["periodTime-"+str(i)])
						statusDict[data["name-"+str(i)]] = int(data["status-"+str(i)])
						subDict[data["name-"+str(i)]] = data["subname-"+str(i)]
			except:
				result['status'] = u"值班时间输入有误"
				json = simplejson.dumps(result)
				return HttpResponse(json, mimetype='application/json')

			#插入到Check表
			newCheck.save()
			lastCheck = Check.objects.latest('id')

			#判断请假缺勤等情况
			pList = User.objects.filter(name__in=nameList, erase=0)
			for p in pList:
				#正常，插入到UserCheck表
				if statusDict[p.name] == 0:
					newUC = UserCheck(FK_user=p, FK_check=lastCheck, timePeriod=timeDict[p.name])
					newUC.save()
				#请假
				elif statusDict[p.name] == 1:
					newLeave = Leave(FK_user=p, FK_check=lastCheck, sub=subDict[p.name])
					newLeave.save()
				#缺勤
				elif statusDict[p.name] == 2:
					newAb = Absence(FK_user=p, FK_check=lastCheck)
					newAb.save()

			#向Ticket表插入
			for i in range(ticketNum):
				if data["ticketNum-"+str(i)]:
					tNum = data["ticketNum-"+str(i)]
					reason = data["reason-"+str(i)]
					way = data["way-"+str(i)]
					dealers = data["dealername-"+str(i)]
					dealers = dealers.split()
					newTicket = Ticket(ticketNum=tNum, FK_check=lastCheck, reason=reason, way=way)
					newTicket.save()
					lastTicket = Ticket.objects.get(ticketNum=tNum)
					pList = User.objects.filter(name__in=dealers, erase=0)
					for p in pList:
						newUT = UserTicket(FK_user=p, FK_ticket=lastTicket)
						newUT.save()
			result['success'] = True
			result['status'] = "OK"
		else:
			result['status'] = u"该时段签到已经存在"
	
	json = simplejson.dumps(result)
	return HttpResponse(json, mimetype='application/json')

def viewCheck(request, page=1):
	if checkLogin(request):
		if page is None or page == "0":
			page = 1
		else:
			page = int(page)
		cList = Check.objects.filter(erase=0)
		checkNum = len(cList)

		if (page - 1)*10 < checkNum:
			start = (page - 1)*10
			pList = Check.objects.filter(erase=0).order_by('id').reverse()[start:start+10]
			for p in pList:
				p.checkDate = str(p.checkDate)
				p.periodType = types[p.periodType-1]
			tmp = checkNum/10
			if checkNum%10 != 0:
				tmp = tmp + 1
			numList = [ i+1 for i in range(tmp) ]
			return render_to_response("wm/viewcheck.html", {'items':pList,'numList':numList, 'now':page})
		elif checkNum == 0:
			return render_to_response("wm/viewcheck.html", {'error':u"无签到信息"})
		else:
			return HttpResponseRedirect("/wm/viewcheck/1/")
	else:
		return HttpResponseRedirect("/wm/login/")

def detail(request, cid):
	if checkLogin(request):
		error = False
		try:
			c = Check.objects.get(id=cid, erase=0)
		except ObjectDoesNotExist:
			error = True
		if not error:
			ucList = UserCheck.objects.filter(FK_check=c)
			lList = Leave.objects.filter(FK_check=c)
			tList = Ticket.objects.filter(FK_check=c)
			aList = Absence.objects.filter(FK_check=c)
			c.checkDate = str(c.checkDate)
			c.periodType = types[c.periodType-1]
			for t in tList:
				t.namelist = []
				utList = UserTicket.objects.filter(FK_ticket=t)
				for ut in utList:
					t.namelist.append(ut.FK_user.name)
			dataDict = {'check':c,'ucList':ucList,'tList':tList,'lList':lList,'aList':aList,'user':request.session['user']}
			return render_to_response("wm/detail.html", dataDict, context_instance=RequestContext(request))
		else:
			return HttpResponseRedirect("/wm/viewcheck/")
	else:
		return HttpResponseRedirect("/wm/login/")

def delete(request):
	if checkLogin(request) and request.session['user'].role == 'black' and request.method == "POST":
		try:
			cid = int(request.POST['cid'])
			c = Check.objects.get(pk=cid, erase=0)
		except:
			back = [u'删除失败']
			return render_to_response("wm/fallback.html", {'back':back})

		ucList = UserCheck.objects.filter(FK_check=c)
		lList = Leave.objects.filter(FK_check=c)
		aList = Absence.objects.filter(FK_check=c)
		tList = Ticket.objects.filter(FK_check=c)
		#增加了erase字段，以下注释掉
		#for t in tList:
		#	utList = UserTicket.objects.filter(FK_ticket=t)
		#	utList.delete()
		#tList.delete()
		#aList.delete()
		#lList.delete()
		#ucList.delete()
		#c.delete()
		Check.objects.filter(pk=cid, erase=0).update(erase=1)
		return HttpResponseRedirect("/wm/viewcheck/1/")
	else:
		return HttpResponseRedirect("/wm/index/")

def ot(request):
	if checkLogin(request):
		if request.session['user'].role in ['mm', 'black'] and request.method == "POST":
			#otF = otForm(request.POST)
			#if otF.is_valid():
			#	data = otF.cleaned_data
			#	uList = User.objects.filter(name=data['name'])
			#	if len(uList) > 0:
			#		newOt = Ot(FK_user=uList[0],hours=data['hours'], otTime=data['otTime'], detail=data['detail'])
			#		newOt.save()
			#		return HttpResponse(u"添加成功")
			#	else:
			#		return HttpResponse(u"查无此人")
			#else:
			#	otF = otForm()
			#	return render_to_response("wm/ot.html", {'form':otF}, context_instance=RequestContext(request))
			data = request.POST
			if data['detail'] == '' or data['otTime'] == '':
				return HttpResponseRedirect("/wm/ot/")
			try:
				lineNum = int(data['lineNum'])
				detail = data['detail']
				otTime = data['otTime'].strip()
				hoursList = []
				nameList = []
				for i in range(lineNum):
					hoursList.append(float(data['hours-'+str(i)].strip()))
					tmp = data['namelist-'+str(i)].strip().split()
					nameList.append(tmp)
			except:
				back = [u'提交参数有误,时间要为数字']
				return render_to_response("wm/fallback.html", {'back':back})

			for i in range(len(nameList)):
				if len(nameList[i]) > 0:
					uList = User.objects.filter(name__in=nameList[i], erase=0)
					for u in uList:
						newOt = Ot(FK_user=u, hours=hoursList[i], otTime=otTime, detail=detail, erase=0)
						newOt.save()

			back = [u'添加成功']
			return render_to_response("wm/fallback.html", {'back':back})
		else:
			otF = otForm()
			return render_to_response("wm/ot.html", {'form':otF}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/login/")

def chargerOt(name, year, month):
	user = User.objects.filter(name=name, erase=0)
	if len(user) == 1 and user[0].role in ['charger','black']:
		oldList = Ot.objects.filter(FK_user=user[0], otTime=datetime.date(year, month, 1), hours=5, detail=u"负责人", erase=0)
		if len(oldList) > 0:
			error = "已经添加了该用户加班信息"
			return error
		else:
			newOt = Ot(FK_user=user[0], otTime=datetime.date(year, month, 1), hours=5,detail=u"负责人", erase=0)
			newOt.save()

	else:
		error = "没有该用户"
		return error

def getStat(name, year, month, startDate, endDate):
	user = User.objects.filter(name=name, erase=0)
	#oldList = Salary.objects.filter(FK_user=user[0])
	if len(user) > 1:
		result = ['fail', name]
		return result
	else:
		start = startDate
		end = endDate
		cList = Check.objects.filter(checkDate__range=(start, end), erase=0)
		ucList = UserCheck.objects.filter(FK_user=user[0], FK_check__in=cList)
		day = 0
		night = 0
		for uc in ucList:
			if uc.FK_check.periodType in [1,2,3,4]:
				day = day + uc.timePeriod
			else:
				night = night + uc.timePeriod

		lList = Leave.objects.filter(FK_user=user[0], FK_check__in=cList)
		aList = Absence.objects.filter(FK_user=user[0], FK_check__in=cList)
		tList = Ticket.objects.filter(FK_check__in=cList)
		utList = UserTicket.objects.filter(FK_user=user[0], FK_ticket__in=tList)

		otList = Ot.objects.filter(FK_user=user[0], otTime__range=(start, end), erase=0)

		leave = len(lList)
		absence = len(aList)
		if absence > 0:
			fullwork = 0
		else:
			for l in lList:
				if l.sub != '':
					leave = leave - 1
			if leave == 0 and day+night > 0:
				fullwork = 1
			else:
				fullwork = 0

		ticket = len(utList)
		otHours = 0
		for o in otList:
			otHours = otHours + o.hours

		if user[0].role == 'charger' and night+day > 0:
			charger = 1
		else:
			charger = 0

		total = day + night - leave*0.5 - absence*1 + fullwork*5 + charger*5 + ticket + otHours
		result = ['succeed', name, year, month, start, end, day, night, ticket, otHours, fullwork, charger, leave, absence, total]
		return result

def insertSalary(result):
	if result[0] == "succeed":
		user = User.objects.filter(name=result[1], erase=0)[0]
		oldList = Salary.objects.filter(FK_user=user, year=result[2], month=result[3], erase=0)
		if len(oldList) == 0:
			newSalary = Salary(FK_user=user, year=result[2], month=result[3], startDate=result[4], endDate=result[5], dayTime=result[6], nightTime=result[7], ticket=result[8], ot=result[9], fullWork=result[10], charger=result[11], leave=result[12], absence=result[13], total=result[14], erase=0)
			newSalary.save()
			return True
		else:
			return False
	else:
		return False

def getSalary(request, mode):
	if checkLogin(request):
		if request.method == "POST" and request.session['user'].role == 'black':
			if mode == "0":
				ssF = salarySingleForm(request.POST)
				if ssF.is_valid():
					data = ssF.cleaned_data
					result = getStat(data['name'], data['year'], data['month'], data['startDate'], data['endDate'])
					if insertSalary(result):
						back = [u'插入成功']
						return render_to_response("wm/fallback.html", {'back':back})
					else:
						if result[0] == 'fail':
							back = [u"用户名"+result[1]+u"错误"]
							return render_to_response("wm/fallback.html", {'back':back})
						else:
							back = [result[1]+str(result[2])+u'年'+str(result[3])+u'月的工资记录已经存在']
							return render_to_response("wm/fallback.html", {'back':back})
				else:
					return HttpResponseRedirect("/wm/getsalary/0/")
			else:
				saF = salaryAllForm(request.POST)
				if saF.is_valid():
					data = saF.cleaned_data
					allUserList = User.objects.filter(erase=0)
					back = []
					for u in allUserList:
						result = getStat(u.name, data['year'], data['month'], data['startDate'], data['endDate'])
						if not insertSalary(result):
							if result[0] == 'fail':
								back.append(u"用户名"+result[1]+u"错误")
							else:
								back.append(result[1]+str(result[2])+u'年'+str(result[3])+u'月的工资记录已经存在')
					if len(back) == 0:
						back = [u"全部插入成功"]
						return render_to_response("wm/fallback.html", {'back':back})
					else:
						return render_to_response("wm/fallback.html", {'back':back})
				else:
					return HttpResponseRedirect("/wm/getsalary/1/")
		else:
			if mode == "0":
				sF = salarySingleForm()
			else:
				sF = salaryAllForm()
			return render_to_response("wm/getsalary.html", {'form':sF, 'mode':mode}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/login/")

def allSalary(request, page="0"):
	if checkLogin(request):
		oldList = Salary.objects.raw("select id, year, month from wm_salary where erase=0 group by year, month desc")
		items = 0
		for o in oldList:
			items = items + 1
		pages = items/12
		if items  % 12 != 0 or items  == 0:
			pages = pages + 1
		pageNum = [ i+1 for i in range(pages) ]
		if page is None or page in ['0', '1'] or int(page) > pages:
			page = 1
			now = page
		return render_to_response("wm/allsalary.html", {'pList':oldList, 'pageNum':pageNum, 'now':page})
	else:
		return HttpResponseRedirect("/wm/login/")

def sByMonth(request, year, month):
	if checkLogin(request):
		try:
			year = int(year)
			month = int(month)
		except:
			back = [u'年份或月份不正确']
			return render_to_response("wm/fallback.html", {'back':back})
		sList = Salary.objects.filter(year=year,month=month, erase=0).order_by()
		for s in sList:
			s.startDate = str(s.startDate)
			s.endDate = str(s.endDate)
		if len(sList) == 0:
			return HttpResponseRedirect("/wm/allsalary/1/")
		else:
			role = request.session['user'].role
			return render_to_response("wm/sbymonth.html", {'sList':sList, 'year':year, 'month':month, 'role':role}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/login/")

def delSalary(request):
	if checkLogin(request):
		if request.session['user'].role == 'black' and request.method == "POST":
			data = request.POST
			try:
				year = int(data['year'])
				month = int(data['month'])
			except:
				back = [u'年份或月份不正确']
				return render_to_response("wm/fallback.html", {'back':back})
			toDelList = Salary.objects.filter(year=year, month=month, erase=0)
			toDelList.update(erase=1)
			return HttpResponseRedirect("/wm/allsalary/")
		else:
			return HttpResponseRedirect("/wm/allsalary/")
	else:
		return HttpResponseRedirect("/wm/login/")

def download(request):
	if checkLogin(request):
		if request.method == "POST":
			year = request.POST['year']
			month = request.POST['month']
			response = HttpResponse(mimetype='text/csv')
			response.write('\xEF\xBB\xBF')
			response['Content-Disposition'] = 'attachment; filename='+year+'-'+month+'.csv'
			sList = Salary.objects.filter(year=year, month=month, erase=0)
			for s in sList:
				s.name = s.FK_user.name.encode('utf-8')
				#s.stuNum = s.FK_user.stuNum.encode('utf-8')
				tmp = "	"+s.FK_user.stuNum
				s.stuNum = tmp.encode('utf-8')
				s.startDate = str(s.startDate).encode('utf-8')
				s.endDate = str(s.endDate).encode('utf-8')

			writer = csv.writer(response, quoting=csv.QUOTE_NONE)
			writer.writerow(['学号','姓名','开始日期','结束日期','前台值班','晚班','Ticket','加班','全勤','负责人','请假','缺勤','总工时'])
			for s in sList:
				writer.writerow([s.stuNum,s.name,s.startDate,s.endDate,s.dayTime,s.nightTime,s.ticket,s.ot,s.fullWork,s.charger,s.leave,s.absence,s.total])

			return response
		else:
			return HttpResponseRedirect("/wm/allsalary/")
	else:
		return HttpResponseRedirect("/wm/login/")
