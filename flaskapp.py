#!/usr/bin/python2
from flask import Flask, request, render_template
import requests
import sys
import datetime, time
import os.path, locale

#Keep track of how many requests are made.
global tbaRequests
tbaRequests = 0
with open(("tbaRequests.txt"), "r") as f:
	tbaRequests = int(f.read())

#Set current year.
#year = str(datetime.datetime.today().year)
year=  "2017"
#Set how wide the table is, equal to bestWorst*2 + 1 (team)
bestWorst = 4

baseURL = 'http://www.thebluealliance.com/api/v2/'
header = {'X-TBA-App-Id': 'tjf:particleprescouter:hackkean3b'} #Yay, version strings....

def matchLogic(match, team, key):
	matchTest = []
	team="frc"+str(team)
	if match['score_breakdown']:
		matchSeries = match['key']
		if team in match['alliances']['red']['teams']:
			redScoreNoFouls = (match['score_breakdown']['red']['totalPoints'] - match['score_breakdown']['red']['foulPoints'] )
			matchTest.append((matchSeries, redScoreNoFouls))
		if team in match['alliances']['blue']['teams']:
			blueScoreNoFouls = (match['score_breakdown']['blue']['totalPoints'] - match['score_breakdown']['blue']['foulPoints'] )
			matchTest.append((matchSeries, blueScoreNoFouls))
	return matchTest
			
def tbaMatch(match):
	t = "https://thebluealliance.com/match/" + match
	return t

def tbaTeam(team):
	team = str(team)
	t = "https://thebluealliance.com/team/" + team
	return t

def getTeamsAtEvent(key):
	tbaIncrement()
	myR = (baseURL + 'event/' + key + '/teams')
	re = requests.get(myR, headers=header)
	teams = re.json()
	teamList=[]
	for t in teams:
		teamList.append((t['team_number']))
	teamList = sorted(teamList)
	return teamList

def getTeamMatchesAtEvent(i, key):
	tbaIncrement()
	myRequest = (baseURL + 'team/frc'+ str(i) + '/event/' + key + '/matches')
	response = requests.get(myRequest, headers=header)
	events = response.json()

	eventMatches = []

	for match in events:
		eventMatches.extend(matchLogic(match, i, key))
	return eventMatches

def tbaIncrement():
	global tbaRequests
	tbaFile = open(("tbaRequests.txt"), "w+")
	tbaFile.write(str(tbaRequests))
	tbaFile.close()
	tbaRequests+=1

def tbaIncGet():
	global tbaRequests
	return format(tbaRequests,',d')

def getEvent(teams, eventCode):
	finalOut=""
	tbaIncrement()
	finalOut += "<h1 style=\"text-align:center\">" + eventCode.upper() + " Event</h1>"
	finalOut += "<table class=\"center\" style=\"width:auto;\">"

	#Generates The Header for the Event
	finalOut+="<tr><th>Team No.</th>"
	for num in range(bestWorst):
		finalOut+="<th>#" + str(num+1) + " Best Match</th>"
	for num in reversed(range(bestWorst)):
		finalOut+="<th>#" + str(num+1) + " Worst Match</th>"
	finalOut+="</tr>"

	#Generates the data for each team at the event.
	for i in teams:	
		print(str(i))
		tbaIncrement()
		myRequest = (baseURL + 'team/frc'+ str(i) + '/'+ year + '/events')
		response = requests.get(myRequest, headers=header)
		jsonified = response.json()
		teamMatches = []
		for thing in jsonified:
			teamMatches.extend(getTeamMatchesAtEvent(i, str(thing['key'])))
		teamMatches = [x for x in teamMatches if x]

		for t in teamMatches:
			print(t)
		if teamMatches != []:		#If they're not empty.
			teamMatches.sort(key=lambda x: x[0][1])
		finalOut+="<tr><td><a href=\"" + tbaTeam(i) + "\">" + str(i) + "</td>"
		for gMatch in teamMatches[-bestWorst:]:
			finalOut+=("<td><a href=\""  + tbaMatch(gMatch[0]) + "\">" + gMatch[0] + "</td>")
		for badMatch in teamMatches[:bestWorst]:
			finalOut+=("<td><a href=\""  + tbaMatch(badMatch[0]) + "\">" + badMatch[0] + "</td>")
		if (len(teamMatches) == 0):
			finalOut+=("<td colspan="+  str(bestWorst*2)+ ">" + "No matches played yet, check back later." +"</td>")
		finalOut+=("</tr>")
	if teams == []:
		finalOut+="<tr><td colspan="+  str((bestWorst*2)+1)+ ">No teams have been populated for this event.</td><tr>"
	finalOut+="</table>"
	finalOut+="<h6 style=\"text-align:center;\">Page generated at: " + str(datetime.datetime.now()) + "</h6>"

	#Archives Data to File
	return finalOut

def frontPage():
	myRequest = (baseURL + "events/"+ str(year))
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	jsonified.sort(key=lambda r: r['end_date'])
	finalOut="<h1 style=\"text-align:center\">Particle Prescouter</h1><h3 style=\"text-align:center\">FIRST Robotics Competition</h3>"
	finalOut+="<table class=\"center\">"
	finalOut+="<tr><th>Week No.</th><th>Event Short Name</th><th>Event Location</th></tr>"
	for t in jsonified:
		#Week off-by-one Corrector
		if t['week'] in range(-1,10):
			t['week']+=1

		#Preseasons
		if time.strptime(str(t['start_date']), "%Y-%m-%d") < time.strptime( year + "-03-01", "%Y-%m-%d"):
			t['week'] = "Preseason"

		#Offseasons
		if time.strptime(str(t['start_date']), "%Y-%m-%d") > time.strptime(year + "-04-26", "%Y-%m-%d"):
			t['week'] = "Offseason"
		#Champs Codes
		if( t['event_code'] == "cmptx" or t['event_code'] == "cmpmo"):
			t['week'] = "Champs"

		finalOut+="<tr><td>"+ str(t['week'])+ "</td><td><a href=\"events/" + t['key'] + "\">" + t['short_name'] + " (" + t['event_code'].upper() + ")</a></td><td>" + t['location'] + "</td></tr>"
	finalOut+="</table>"
	finalOut+="<h6 style=\"text-align:center\">" + tbaIncGet() + " Requests to TBA (And Counting!)</h6>"
	return finalOut

def file_len(fname):
	with open(fname) as f:
		for i, l in enumerate(f):
			pass
	return i + 1

def savePage():
	print("Started at "+  str(datetime.datetime.now()))
	myRequest = (baseURL + "events/"+ str(year))
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	for r,t in enumerate(jsonified):
		if not(os.path.isfile(str("export/" + t['key'] + ".html"))):
			f = open(("./export/" + t['key'] + ".html"), "w+")
			f.write(scoutatevent(t['key']))
			print("Updating " + t['key'].upper() + " via cache view.")
			print(str(r) +"/"+  str(len(jsonified)))
			f.close()
		elif (open("./export/" + t['key'] + ".html").read() == ""):
			f = open(("./export/" + t['key'] + ".html"), "w+")
			f.write(scoutatevent(t['key']))
			print("Updating " + t['key'].upper() + " via cache view.")
			print(str(r) +"/"+  str(len(jsonified)))
			f.close()
	print("Finished @ " + str(datetime.datetime.now()))

def statsTest():
	finalOut="<h4>" + tbaIncGet()  +" requests to The Blue Alliance and counting!</h4>"
	finalOut+="<h4>" + str(file_len("./flaskapp.py")) + " lines of code in this project.</h4>"
	finalOut+="<form action=\"admin/save/\" method=\"post\"><button name=\"foo\" value=\"upvote\">Save Entire Site to Static</button></form>"

	return finalOut
	

app = Flask(__name__)

@app.route('/')
def getEvents():
	return render_template("base.html", bodyhtml = frontPage())

#Event is LIVE
@app.route('/event/<event>')
def scoutatevent(event):
	holder = render_template("base.html", bodyhtml =getEvent(getTeamsAtEvent(event),event))
	with open(("./export/" + event + ".html"), "w+") as f:
		f.write(holder)
	print("Updating " + event.upper() + " via non-static view.")
	return holder

#Events is STATIC
@app.route('/events/<event>')
def scoutatevents(event):
	with open(("./export/" + event + ".html"), "r") as f:
		return f.read()

#Stats Page
@app.route('/stats')
def simplestats():
	return render_template("base.html", bodyhtml=statsTest())

#SAVE EVERYTHING
@app.route('/admin/save/', methods=['POST'])
def saveEvents():
	savePage()
	return ''

@app.route('/cdr/')
def cdr():
	teamList = []
	myRequest = (baseURL + 'districts/2017')
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	for district in jsonified:
		myRequest = (baseURL + 'district/' + district['key'] + '/2017/rankings')
		response = requests.get(myRequest, headers=header)
		json2 = response.json()
		for i in json2:
			teamList.append((i['team_key'], i['point_total'], district['key']))
	teamList.sort(key=lambda x: x[1])
	teamList = reversed(teamList)
	hold=1
	finalOut="<table class=\"center\" style=\"width:auto;\"><tr><th>Rank</th><th>Team No.</th><th>No. Pts.</th><th>Dist. Code</th></tr>\n"
	for i in teamList:
		finalOut+="<tr><td>" + str(hold) + "</td><td>" + str(i[0]).upper() + "</td><td>" + str(i[1]) + "</td><td>" + str(i[2]).upper() + "</td></tr>"
		hold+=1
	finalOut+="</table>"
	return render_template("base.html", bodyhtml=finalOut)

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
	return render_template('500.html'), 500

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
