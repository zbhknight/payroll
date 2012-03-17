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
		popOut = 'yes'
		nextJump = '/wm/login/'
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
						eMsg = u'与ECNC同步成功，请用学号和ECNC密码登录'
						return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
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
		return render_to_response("wm/check.html", {'checkForm':cF, 'user':request.session['user']})
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
		paramDict = {"formset":nFs,"count":count,"dayType":dayType,'one':wday,'two':ptype, 'user':request.session['user']}
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

			return render_to_response("wm/plan.html", {"types":types, "days":days, "allDict":allDict, 'user':request.session['user']})
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
				if len(pList) > 0:
					nameList = [ p.FK_user.name for p in pList ]
					index = [ i for i in range(len(nameList)) ]
					nameDict = dict(zip(index, nameList))
					result['success'] = "True"
					result['namelist'] = nameList
					result['num'] = len(nameList)
					result['wday'] = wday
					if (wday == 6 or wday == 7) and (ptype == 1 or ptype == 3):
						flag = pHour.objects.filter(ptype=ptype+5)[0]
					else:
						flag = pHour.objects.filter(ptype=ptype)[0]
					result['hour'] = flag.hour
					result.update(nameDict)
				else:
					result['status'] = u'该时段并无值班人员'
				
		else:
			result['status'] = u'时间为空'
	elif request.method == "GET":
		result['success'] = True
		result['date'] = request.POST['date']
	json = simplejson.dumps(result)
	return HttpResponse(json, mimetype='application/json')

def test(request):
	if request.method == "POST":
		fF = fileForm(request.POST, request.FILES)
		if fF.is_valid():
			f = request.FILES['file']
			target = open("wm/static/test.csv", 'wb+')
			for chunk in f.chunks():
				target.write(chunk)
			target.close()
			reader = csv.reader(open("wm/static/test.csv", 'rb'))
			lines = [ ' '.join(row).decode('GBK').replace('*','').split(' ') for row in reader ]
			#lines = [] 
			#for row in reader:
			#	tmp = []
			#	for i in row:
			#		tmp.append(i.decode('GBK').encode('utf-8'))
			#	lines.append(tmp)
			return HttpResponse(lines)
		else:
			return HttpResponse("NOOOO")
	else:
		fF = fileForm()
		return render_to_response("wm/test.html", {'form':fF}, context_instance=RequestContext(request))


def userExist(name):
	uList = User.objects.filter(name=name)
	if len(uList) > 0:
		return True
	else:
		return False

def testTicket(data, ticketNum, prefix1, prefix2):
	status = ['','','']
	testTNum = []
	for i in range(ticketNum):
		if data[prefix1+str(i)] != '':
			if data[prefix1+str(i)] in testTNum:
				status[0] = u'提交重复的Ticket号' 
				return status
			else:
				testTNum.append(data[prefix1+str(i)])

			tNum = data[prefix1+str(i)]
			tList = Ticket.objects.filter(ticketNum=tNum)
			if len(tList) > 0:
				status[1] += ' ' + tNum
			dealers = data[prefix2+str(i)]
			dealers = dealers.split()
			pList = User.objects.filter(name__in=dealers, erase=0)
			if len(pList) < len(dealers):
				status[2] += tNum + u'处理人名字有误'
	return status

def insertTicket(data, ticketNum, lastcheck):
	for i in range(ticketNum):
		if data["ticketNum-"+str(i)] != '':
			tNum = data["ticketNum-"+str(i)]
			reason = data["reason-"+str(i)]
			way = data["way-"+str(i)]
			dealers = data["dealername-"+str(i)]
			dealers = dealers.split()
			newTicket = Ticket(ticketNum=tNum, FK_check=lastcheck, reason=reason, way=way)
			newTicket.save()
			lastTicket = Ticket.objects.get(ticketNum=tNum)
			pList = User.objects.filter(name__in=dealers, erase=0)
			for p in pList:
				newUT = UserTicket(FK_user=p, FK_ticket=lastTicket)
				newUT.save()

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

			#检测ticket是否重复
			status = testTicket(data, ticketNum,"ticketNum-","dealername-")
			if status[0] != '':
				result['status'] = status[0]
				json = simplejson.dumps(result)
				return HttpResponse(json, mimetype='application/json')
			elif status[1] != '':
				result['status'] = u'Ticket' + status[1] + u'信息已存在，请确认输入无误\n' + status[2]
				json = simplejson.dumps(result)
				return HttpResponse(json, mimetype='application/json')
			elif status[2] != '':
				result['status'] = status[2]
				json = simplejson.dumps(result)
				return HttpResponse(json, mimetype='application/json')


			error = False
			#检测输入的名字是否重复或者错误
			if len(nameList) != len(set(nameList)):
				result['status'] = u'签到名字有重复'
				error = True
			else:
				pList = User.objects.filter(name__in=nameList, erase=0)
				if len(pList) < len(nameList):
					result['status'] = u'签到输入的名字有误'
					error = True
			if error:
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
					if userExist(subDict[p.name]):
						subtmp = subDict[p.name]
					else:
						subtmp = ''
					newLeave = Leave(FK_user=p, FK_check=lastCheck, sub=subtmp)
					newLeave.save()
				#缺勤
				elif statusDict[p.name] == 2:
					newAb = Absence(FK_user=p, FK_check=lastCheck)
					newAb.save()

			#向Ticket表插入
			for i in range(ticketNum):
				if data["ticketNum-"+str(i)] != '':
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
			result['id'] = lastCheck.id
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
			pList = Check.objects.filter(erase=0).order_by('checkDate').reverse()[start:start+10]
			for p in pList:
				p.checkDate = str(p.checkDate)
				p.periodType = types[p.periodType-1]
			tmp = checkNum/10
			if checkNum%10 != 0:
				tmp = tmp + 1
			numList = [ i+1 for i in range(tmp) ]
			return render_to_response("wm/viewcheck.html", {'items':pList,'numList':numList, 'now':page, 'user':request.session['user']})
		elif checkNum == 0:
			return render_to_response("wm/viewcheck.html", {'error':u"无签到信息", 'user':request.session['user']})
		else:
			return HttpResponseRedirect("/wm/viewcheck/1/")
	else:
		return HttpResponseRedirect("/wm/login/")

def viewOt(request, page=1):
	if checkLogin(request):
		if page is None or page == "0":
			page = 1
		else:
			page = int(page)
		oList = Ot.objects.filter(erase=0)
		otNum= len(oList)

		if (page - 1)*20 < otNum:
			start = (page - 1)*20
			pList = Ot.objects.filter(erase=0).order_by('otTime').reverse()[start:start+20]
			for p in pList:
				p.otTime = str(p.otTime)
			tmp = otNum/20
			if otNum%20 != 0:
				tmp = tmp + 1
			numList = [ i+1 for i in range(tmp) ]
			return render_to_response("wm/viewot.html", {'items':pList,'numList':numList, 'now':page,'user':request.session['user']}, context_instance=RequestContext(request))
		elif otNum == 0:
			return render_to_response("wm/viewot.html", {'error':u"无加班信息", 'user':request.session['user']})
		else:
			return HttpResponseRedirect("/wm/viewot/1/")
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
		popOut = 'yes'
		nextJump = '/wm/viewcheck/1/'
		try:
			cid = int(request.POST['cid'])
			c = Check.objects.get(pk=cid, erase=0)
		except:
			eMsg = u'删除签到失败'
			return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})

		ucList = UserCheck.objects.filter(FK_check=c)
		lList = Leave.objects.filter(FK_check=c)
		aList = Absence.objects.filter(FK_check=c)
		tList = Ticket.objects.filter(FK_check=c)
		#增加了erase字段，以下注释掉
		for t in tList:
			utList = UserTicket.objects.filter(FK_ticket=t)
			utList.delete()
		tList.delete()
		#aList.delete()
		#lList.delete()
		#ucList.delete()
		#c.delete()
		Check.objects.filter(pk=cid, erase=0).update(erase=1)
		return HttpResponseRedirect("/wm/viewcheck/1/")
	else:
		return HttpResponseRedirect("/wm/index/")

def delOt(request):
	if checkLogin(request):
		if request.method == "POST" and request.session['user'].role == 'black':
			nextJump = "/wm/viewot/1/"
			popOut = 'yes'
			try:
				otid = request.POST['otid']
			except:
				eMsg = u'加班信息出错'
				return render_to_response("wm/fallback.html", {'eMsg':eMsg})

			oList = Ot.objects.filter(id=otid)
			if len(oList) == 1:
				oList.update(erase=1)
				eMsg = u'加班记录删除成功'
			else:
				eMsg = u'加班信息出错'
			return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg, 'nextJump':nextJump})
		else:
			return HttpResponseRedirect("/wm/viewot/1/")
	else:
		return HttpResponseRedirect("/wm/login/")

def ot(request):
	if checkLogin(request):
		if request.session['user'].role in ['mm', 'black'] and request.method == "POST":
			popOut = 'yes'
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
				tmp = time.strptime(otTime, "%Y-%m-%d %H:%M:%S")
				otTime = datetime.datetime(* tmp[:6])
				hoursList = []
				nameList = []
				for i in range(lineNum):
					hoursList.append(float(data['hours-'+str(i)].strip()))
					tmp = data['namelist-'+str(i)].strip().split()
					nameList.append(tmp)
			except:
				nextJump = '/wm/ot/'
				eMsg = u'提交参数有误,加班时长要为数字,加班时间请按照示例格式 '
				return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})

			eMsg = ''
			for i in range(len(nameList)):
				if len(nameList[i]) > 0:
					uList = User.objects.filter(name__in=nameList[i], erase=0)
					if len(uList) < len(nameList[i]):
						eMsg += u'第'+str(i+1)+u'行姓名输入错误;'

			if eMsg != '' or lineNum == 0:
				eMsg += u'未能成功插入'
				nextJump = '/wm/ot/'
				return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
			else:
				for i in range(len(nameList)):
					if len(nameList[i]) > 0:
						uList = User.objects.filter(name__in=nameList[i], erase=0)
						for u in uList:
							newOt = Ot(FK_user=u, hours=hoursList[i], otTime=otTime, detail=detail, erase=0)
							newOt.save()

			eMsg = u'添加成功'
			nextJump = '/wm/viewot/1/'
			return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
		else:
			otF = otForm()
			return render_to_response("wm/ot.html", {'form':otF, 'user':request.session['user']}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/login/")

def specialOt(year, month, role, hours):
	#user = User.objects.filter(name=name, erase=0)
	#if len(user) == 1 and user[0].role in ['charger','black']:
	#	oldList = Ot.objects.filter(FK_user=user[0], otTime=datetime.date(year, month, 1), hours=5, detail=u"负责人", erase=0)
	#	if len(oldList) > 0:
	#		error = "已经添加了该用户加班信息"
	#		return error
	#	else:
	#		newOt = Ot(FK_user=user[0], otTime=datetime.date(year, month, 1), hours=5,detail=u"负责人", erase=0)
	#		newOt.save()

	#else:
	#	error = "没有该用户"
	#	return error
	nTime = datetime.date(year, month, 1)
	detailList = [u'负责人',u'内务组']
	otList = Ot.objects.filter(otTime=nTime, detail__in=detailList, erase=0)
	if role == "mm":
		detail= u"内务组"
	else:
		detail = u'负责人'
	if len(otList) == 0:
		uList = User.objects.filter(role=role, erase=0)
		for u in uList:
			newOt = Ot(FK_user=u, otTime=nTime, hours=hours, detail=detail, erase=0)
			newOt.save()
		result = True
	else:
		result = False
	
	return result

def getStat(name, year, month, startDate, endDate):
	user = User.objects.filter(name=name, erase=0)
	#oldList = Salary.objects.filter(FK_user=user[0])
	if len(user) != 1:
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

		total = day + night - leave*0.5 - absence*1 + fullwork*5 + ticket + otHours
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
				popOut = 'yes'
				nextJump = '/wm/getsalary/0/'
				ssF = salarySingleForm(request.POST)
				if ssF.is_valid() and ssF.cleaned_data['month'] < 100:
					data = ssF.cleaned_data
					result = getStat(data['name'], data['year'], data['month'], data['startDate'], data['endDate'])
					if insertSalary(result):
						eMsg = u'插入成功'
					else:
						if result[0] == 'fail':
							eMsg = u"用户名"+result[1]+u"错误"
						else:
							eMsg = result[1]+str(result[2])+u'年'+str(result[3])+u'月的工资记录已经存在'
				else:
					eMsg = u'表单不完整或者月份填写错误'
				return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
			else:
				popOut = 'no'
				nextJump = '/wm/getsalary/1/'
				saF = salaryAllForm(request.POST)
				if saF.is_valid() and saF.cleaned_data['month'] < 100:
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
						popOut = 'yes'
						eMsg = u"全部插入成功"
						nextJump = "/wm/allsalary/1/"
						return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
					else:
						return render_to_response("wm/fallback.html", {'back':back})
				else:
					popOut = 'yes'
					nextJump = '/wm/getsalary/1/'
					eMsg = u'表单不完整或者月份填写错误'
					return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
		else:
			if mode == "0":
				sF = salarySingleForm()
			else:
				sF = salaryAllForm()
			return render_to_response("wm/getsalary.html", {'form':sF, 'mode':mode, 'user':request.session['user']}, context_instance=RequestContext(request))
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

		if items == 0:
			error = u'无工资信息'
			return render_to_response("wm/allsalary.html", {'pList':oldList, 'pageNum':pageNum, 'now':page, 'user':request.session['user'], 'error':error})
		else:
			return render_to_response("wm/allsalary.html", {'pList':oldList, 'pageNum':pageNum, 'now':page, 'user':request.session['user']})
	else:
		return HttpResponseRedirect("/wm/login/")

def sByMonth(request, year, month):
	if checkLogin(request):
		try:
			year = int(year)
			month = int(month)
		except:
			popOut = 'yes'
			nextJump = '/wm/allsalary/1/'
			eMsg = u'年份或月份不正确'
			return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
		sList = Salary.objects.filter(year=year,month=month, erase=0).order_by()
		for s in sList:
			s.startDate = str(s.startDate)
			s.endDate = str(s.endDate)
		if len(sList) == 0:
			return HttpResponseRedirect("/wm/allsalary/1/")
		else:
			role = request.session['user'].role
			return render_to_response("wm/sbymonth.html", {'sList':sList, 'year':year, 'month':month, 'role':role, 'user':request.session['user']}, context_instance=RequestContext(request))
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
				popOut = 'yes'
				nextJump = '/wm/allsalary/1/'
				eMsg = u'年份或月份不正确'
				return render_to_response("wm/fallback.html", {'popOut':popOut,'eMsg':eMsg,'nextJump':nextJump})
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

def viewUser(request, page='1'):
	if checkLogin(request) and request.session['user'].role == 'black':
		if page is None or page == "0":
			page = 1
		else:
			page = int(page)
		userNum = User.objects.all().count()

		if (page - 1)*20 < userNum:
			start = (page - 1)*20
			pList = User.objects.all().order_by('stuNum').reverse()[start:start+20]

			for p in pList:
				if p.nickname is not None:
					p.syn = 1
				else:
					p.syn = 0
			tmp = userNum/20
			if userNum%20 != 0:
				tmp = tmp + 1
			numList = [ i+1 for i in range(tmp) ]
			return render_to_response("wm/viewuser.html", {'items':pList,'numList':numList, 'now':page,'user':request.session['user']})
		elif userNum == 0:
			return render_to_response("wm/viewuser.html", {'error':u"无用户信息", 'user':request.session['user']})
		else:
			return HttpResponseRedirect("/wm/viewuser/1/")
	else:
		return HttpResponseRedirect("/wm/index/")

def a_modUser(request):
	result = {}
	result['succeed'] = 'no'
	if checkLogin(request) and request.method == "POST" and request.session['user'].role == 'black':
		try:
			role = int(request.POST['role'])
			roleName = [None, 'charger', 'mm', 'black']
			role = roleName[role]
			erase = int(request.POST['erase'])
			stuNum = str(request.POST['stuNum'])
		except:
			result['error'] = u'赋值错误'
			json = simplejson.dumps(result)
			return HttpResponse(json, mimetype="application/json")

		uList = User.objects.filter(stuNum=stuNum)
		if len(uList) == 1:
			uList.update(role=role, erase=erase)
			result['succeed'] = 'yes'
			if role is not None:
				result['role'] = role
			else:
				result['role'] = u'普通'
			if erase == 0:
				result['erase'] = u'在岗'
			else:
				result['erase'] = u'不在岗'
		else:
			result['error'] = u'用户不存在'
	json = simplejson.dumps(result)
	return HttpResponse(json, mimetype="application/json")

def allRelated(name, sDate, eDate):
	uList = User.objects.filter(name=name)
	if len(uList) != 1:
		result = [False]
	else:
		user = uList[0]
		cList = Check.objects.filter(erase=0, checkDate__range=(sDate, eDate))
		ucList = UserCheck.objects.filter(FK_user=user, FK_check__in=cList)
		tList = Ticket.objects.filter(FK_check__in=cList)
		utList = UserTicket.objects.filter(FK_user=user, FK_ticket__in=tList)
		lList = Leave.objects.filter(FK_check__in=cList)
		aList = Absence.objects.filter(FK_check__in=cList)
		otList = Ot.objects.filter(FK_user=user, otTime__range=(sDate, eDate))

		result = [True, cList, ucList, tList, utList, lList, aList, otList]
	return result

def getAll(request):
	if checkLogin(request):
		if request.method == "POST":
			popOut = 'yes'
			nextJump = '/wm/getall/'
			sF = salarySingleForm(request.POST)
			if sF.is_valid():
				data = sF.cleaned_data
				status = getStat(data['name'], 2012, 2, data['startDate'], data['endDate'])
				if status[0] == 'fail':
					eMsg = u'名字输入有误'
				else:
					tmp = allRelated(data['name'], data['startDate'], data['endDate'])
					result = {}
					result['status'] = status
					result['cList'] = tmp[1]
					result['ucList'] = tmp[2]
					result['tList'] = tmp[3]
					result['utList'] = tmp[4]
					result['lList'] = tmp[5]
					result['aList'] = tmp[6]
					result['otList'] = tmp[7]
					return render_to_response("wm/all.html", result)
			else:
				eMsg = u'输入信息有误'
			return render_to_response("wm/fallback.html", {'popOut':popOut, 'eMsg':eMsg, 'nextJump':nextJump})
		else:
			sF = salarySingleForm()
			return render_to_response("wm/getall.html", {'form':sF, 'user':request.session['user']}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/login/")

def setHour(request):
	if checkLogin(request) and request.session['user'].role == 'black':
		if request.method == "POST":
			shF = setHourForm(request.POST)
			if shF.is_valid():
				tmp = []
				data = shF.cleaned_data
				tmp.append(data['am'])
				tmp.append(data['noon'])
				tmp.append(data['pm'])
				tmp.append(data['nightDesk'])
				tmp.append(data['darkHouse'])
				tmp.append(data['wam'])
				tmp.append(data['wnoon'])
				tmp.append(data['wpm'])
				for i in range(8):
					phList = pHour.objects.filter(ptype=i+1)
					if len(phList) > 0:
						phList.update(hour=tmp[i])
					else:
						newPh = pHour(ptype=i+1, hour=tmp[i], option='')
						newPh.save()
				popOut = 'yes'
				nextJump = '/wm/sethour/'
				eMsg = u'修改成功'
				return render_to_response("wm/fallback.html", {'popOut':popOut, 'eMsg':eMsg, 'nextJump':nextJump})
			else:
				return HttpResponseRedirect("/wm/sethour/")
		else:
			tmp = []
			for i in range(8):
				aTime = pHour.objects.filter(ptype=i+1)
				if len(aTime) > 0:
					tmp.append(aTime[0].hour)
				else:
					tmp.append(0)
			data = {'am':tmp[0],'noon':tmp[1],'pm':tmp[2],'nightDesk':tmp[3],'darkHouse':tmp[4],'wam':tmp[5],'wnoon':tmp[6],'wpm':tmp[7],}

			shF = setHourForm(data)
			return render_to_response("wm/sethour.html", {'form':shF, 'user':request.session['user']}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/index/")

def checkStat(request):
	if checkLogin(request):
		if request.method == 'POST':
			sF = salarySingleForm(request.POST)
			if sF.is_valid():
				data = sF.cleaned_data
				start = data['startDate']
				end = data['endDate']
				baseList = Check.objects.filter(checkDate__range=(data['startDate'], data['endDate']), erase=0)
				if len(baseList) > 0:
					i = 0
					result = []
					while True:
						newDate = start + datetime.timedelta(days=i)
						if newDate <= end:
							newList = baseList.filter(checkDate=newDate).order_by('periodType')
							idList = [ item.id for item in newList ]
							typeList = [ item.periodType for item in newList ]
							tmp = Check(checkDate=newDate, periodType=1, option='', handler=request.session['user'],erase=0)
							tmp.i = i
							tmp.checkDate = str(newDate)
							tmp.wday = days[newDate.weekday()]
							tmp.typelist = typeList
							tmp.idlist = idList
							tmp.dict = dict(zip(typeList, idList))
							result.append(tmp)
							i += 1
						else:
							break
					numList = [ i+1 for i in range(5)]
					choose = 'yes'
					return render_to_response("wm/checkstat.html", {'choose':choose,'result':result,'numList':numList, 'days':days, 'user':request.session['user']})
				else:
					error = True
					popOut = 'yes'
					nextJump = '/wm/checkstat/'
					eMsg = u'该时段并无签到记录'
					return render_to_response("wm/fallback.html", {'popOut':popOut, 'eMsg':eMsg, 'nextJump':nextJump})
			else:
				error = True
				popOut = 'yes'
				nextJump = '/wm/checkstat/'
				eMsg = u'输入有误'
				return render_to_response("wm/fallback.html", {'popOut':popOut, 'eMsg':eMsg, 'nextJump':nextJump})
		else:
			sF = salarySingleForm()
			return render_to_response("wm/checkstat.html", {'form':sF, 'user':request.session['user']}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/login/")

def a_modTicket(request):
	result = {}
	result['succeed'] = 'no'
	if checkLogin(request) and request.session['user'].role in ['mm','black'] and request.method == "POST":
		data = request.POST
		tList = Ticket.objects.filter(ticketNum=data['tNum'])
		if len(tList) > 0:
			dealers = data['dealers'].split()
			uList = User.objects.filter(name__in=dealers, erase=0)
			if len(uList) == len(dealers):
				tList.update(reason=data['reason'],way=data['way'])
				oldList = UserTicket.objects.filter(FK_ticket=tList[0])
				oldList.delete()
				for u in uList:
					newUt = UserTicket(FK_user=u, FK_ticket=tList[0])
					newUt.save()
				result['succeed'] = 'yes'
				result['reason'] = data['reason']
				result['way'] = data['way']
				result['dealers'] = data['dealers']
			else:
				result['status'] = u'输入的处理人名字有误'
		else:
			result['status'] = u'ticket号错误'

		json = simplejson.dumps(result)
		return HttpResponse(json, mimetype="application/json")
	else:
		return HttpResponseRedirect("/wm/index/")

def a_delTicket(request):
	result = {}
	result['succeed'] = 'no'
	if checkLogin(request) and request.session['user'].role in ['mm','black'] and request.method == "POST":
		data = request.POST
		tList = Ticket.objects.filter(ticketNum=data['tNum'])
		if len(tList) > 0:
			oldList = UserTicket.objects.filter(FK_ticket=tList[0])
			oldList.delete()
			tList.delete()
			result['succeed'] = 'yes'
		else:
			result['status'] = u'ticket号错误'

		json = simplejson.dumps(result)
		return HttpResponse(json, mimetype="application/json")
	else:
		return HttpResponseRedirect("/wm/index/")

def a_addTicket(request):
	result = {}
	result['succeed'] = 'no'
	if checkLogin(request) and request.session['user'].role in ['mm','black'] and request.method == "POST":
		data = request.POST
		try:
			ticketNum = int(data['ticketNum'])
			checkId = int(data['checkId'])
		except:
			result['status'] = u'输入数据有错'
			json = simplejson.dumps(result)
			return HttpResponse(json, mimetype="application/json")

		#检测ticket是否重复
		status = testTicket(data, ticketNum,"ticketNum-","dealername-")
		if status[0] != '':
			result['status'] = status[0]
			json = simplejson.dumps(result)
			return HttpResponse(json, mimetype='application/json')
		elif status[1] != '':
			result['status'] = u'Ticket' + status[1] + u'信息已存在，请确认输入无误\n' + status[2]
			json = simplejson.dumps(result)
			return HttpResponse(json, mimetype='application/json')
		elif status[2] != '':
			result['status'] = status[2]
			json = simplejson.dumps(result)
			return HttpResponse(json, mimetype='application/json')

		cList = Check.objects.filter(id=checkId)
		if len(cList) > 0:
			insertTicket(data, ticketNum, cList[0])
			result['succeed'] = 'yes'
			result['checkId'] = data['checkId']
		else:
			result['status'] = u'签到数据出错'

		json = simplejson.dumps(result)
		return HttpResponse(json, mimetype="application/json")
	else:
		return HttpResponseRedirect("/wm/index/")

def otShortcut(request):
	if checkLogin(request) and request.session['user'].role == 'black':
		if request.method == "POST":
			popOut = 'yes'
			nextJump = '/wm/viewot/'
			sotF = specialOtForm(request.POST)
			if sotF.is_valid():
				data = sotF.cleaned_data
				roles = ['charger', 'mm']
				if data['year'] > 0 and data['year'] < 10000 and data['month'] > 0 and data['month'] < 13:
					if specialOt(data['year'], data['month'], roles[int(data['ottype'])], data['hours']):
						eMsg = u'成功添加加班信息'
					else:
						eMsg = u'已存在相同的加班记录'
				else:
					eMsg = u'年份或月份输入有误'
			else:
				eMsg = u'表单提交信息有误，加班时长为数字'
			
			return render_to_response("wm/fallback.html", {'popOut':popOut, 'eMsg':eMsg, 'nextJump':nextJump})
		else:
			sotF = specialOtForm()
			return render_to_response("wm/otshortcut.html", {'form':sotF, 'user':request.session['user']}, context_instance=RequestContext(request))
	else:
		return HttpResponseRedirect("/wm/index/")

def a_getRoleNameList(request):
	result = {}
	result['succeed'] = 'no'
	if checkLogin(request) and request.session['user'].role == 'black':
		if request.method == "POST":
			try:
				ottype = int(request.POST['ottype'])
				hours = float(request.POST['hours'])
			except:
				result['status'] = u'输入的加班类型或加班时长有误'

			roles = ['charger', 'mm']
			role2 = [u'负责人',u'内务组mm']
			uList = User.objects.filter(role=roles[ottype], erase=0)
			nameList = [ u.name for u in uList ]
			result['nameList'] = nameList
			result['hours'] = hours
			result['succeed'] = 'yes'
			result['role'] = role2[ottype]

		json = simplejson.dumps(result)
		return HttpResponse(json, mimetype='application/json')
