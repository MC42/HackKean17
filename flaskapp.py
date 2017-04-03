#!/usr/bin/python2
from flask import Flask, request, render_template
import requests
import sqlite3
import sys
import datetime, time
import os.path, locale	

#Keep track of how many requests are made.
global tbaRequests
tbaRequests = 0
tbaFile = open(("tbaRequests.txt"), "r")
tbaRequests = int(tbaFile.read())
tbaFile.close()

#Set current year for thing.
year = str(datetime.datetime.today().year)
#Set how wide the table is, equal to bestWorst*2 + 1 (team)
bestWorst = 4

baseURL = 'http://www.thebluealliance.com/api/v2/'
header = {'X-TBA-App-Id': 'tjf:particleprescouter:hackkean3'} #Yay, version strings....

def matchLogic(match, team, key):
	team="frc"+str(team)
	if match['score_breakdown']:
		matchSeries = match['key']
		if team in match['alliances']['red']['teams']:
			redScoreNoFouls = (match['score_breakdown']['red']['totalPoints'] - match['score_breakdown']['red']['foulPoints'] )
			cursor.execute("insert into MATCHES VALUES(?,?)", (matchSeries, redScoreNoFouls))
		if team in match['alliances']['blue']['teams']:
			blueScoreNoFouls = (match['score_breakdown']['blue']['totalPoints'] - match['score_breakdown']['blue']['foulPoints'] )
			cursor.execute("insert into MATCHES VALUES(?,?)", (matchSeries, blueScoreNoFouls))
			
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
	for match in events:
		matchLogic(match, i, key)

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
	global conn
	conn = sqlite3.connect(':memory:',detect_types=sqlite3.PARSE_DECLTYPES| sqlite3.PARSE_COLNAMES, check_same_thread=False)
	global cursor
	cursor = conn.cursor()

	cursor.execute('CREATE TABLE `MATCHES` (	`KEY`	TEXT,	`SCORE`	INTEGER);')
	tbaIncrement()
	finalOut ="<link href=\"https://fonts.googleapis.com/css?family=Droid+Sans|Righteous\" rel=\"stylesheet\"><style>table{font-size:14px;}th{text-align:left;}	.center{margin: auto;    border: 3px solid #ff6600;    padding: 10px;border-radius:10px;}body{font-family:'Droid Sans';}h1,h3{font-family:'Righteous';line-height: 70%;}</style>"
	finalOut += "<h1 style=\"text-align:center\">" + eventCode.upper() + " Event</h1>"
	finalOut += "<table class=\"center\" style=\"width:auto%;\">"

	#Generates The Header for the Event
	finalOut+="<tr><th>Team No.</th>"
	for num in range(bestWorst):
		finalOut+="<th>#" + str(num+1) + " Best Match</th>"
	for num in reversed(range(bestWorst)):
		finalOut+="<th>#" + str(num+1) + " Worst Match</th>"
	finalOut+="</tr>"

	#Generates the data for each team at the event.
	for i in teams:	
		tbaIncrement()
		myRequest = (baseURL + 'team/frc'+ str(i) + '/'+ year + '/events')
		response = requests.get(myRequest, headers=header)
		jsonified = response.json()

		for thing in jsonified:
			getTeamMatchesAtEvent(i, str(thing['key']))
		cursor.execute('SELECT * FROM MATCHES ORDER BY SCORE DESC LIMIT ?;', (bestWorst,))
		bestMatches = cursor.fetchall()	
		finalOut+="<tr><td><a href=\"" + tbaTeam(i) + "\">" + str(i) + "</td>"
		for gMatch in bestMatches:
			finalOut+=("<td><a href=\""  + tbaMatch(gMatch[0]) + "\">" + gMatch[0] + "</td>")
		cursor.execute('SELECT * FROM MATCHES ORDER BY SCORE ASC LIMIT ?;', (bestWorst,))
		worstMatches = cursor.fetchall()
		for badMatch in worstMatches:
			finalOut+=("<td><a href=\""  + tbaMatch(badMatch[0]) + "\">" + badMatch[0] + "</td>")
		if (len(worstMatches) == 0):
			finalOut+=("<td colspan="+  str(bestWorst*2)+ ">" + "No matches played yet, check back later." +"</td>")
		finalOut+=("</tr>")
	
		cursor.execute("DELETE FROM MATCHES;")  #CLEANUP FOR NEXT TEAM
	finalOut+="</table>"

	finalOut+="<h6>Page generated at: " + str(datetime.datetime.now()) + "</h6>"

	#Archives Data to File
	f = open(("./export/" + eventCode + ".html"), "w+")
	f.write(finalOut)
	print("Updating " + eventCode.upper() + " via non-static view.")
	f.close()
	return finalOut

def frontPage():
	finalOut = "<link href=\"https://fonts.googleapis.com/css?family=Droid+Sans\" rel=\"stylesheet\"><link href=\"https://fonts.googleapis.com/css?family=Righteous\" rel=\"stylesheet\"> <style>body{font-family:'Droid Sans';}h1,h3{font-family:'Righteous';line-height: 70%;}.center{margin: auto;width: 60%;border:5px solid #ff6600;padding:10px;border-radius:10px;}</style>"
	myRequest = (baseURL + "events/"+ str(year))
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	jsonified.sort(key=lambda r: r['end_date'])
	finalOut+="<h1 style=\"text-align:center\">Particle Prescouter</h1><h3 style=\"text-align:center\">FIRST Robotics Competition</h3>"
	finalOut+="<div class=\"center\"><table style=\"width:100%;\">"
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
			print(t['event_code'])
			t['week'] = "Champs"

		finalOut+="<tr><td>"+ str(t['week'])+ "</td><td><a href=\"events/" + t['key'] + "\">" + t['short_name'] + " (" + t['event_code'].upper() + ")</a></td><td>" + t['location'] + "</td></tr>"
	finalOut+="</table>"
	finalOut+="<h6 style=\"text-align:center\">" + tbaIncGet() + " Requests to TBA (And Counting!)</h6></div>"
	return finalOut

def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def savePage():
	print("Saving entire damn site to static!")
	myRequest = (baseURL + "events/"+ str(year))
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	for t in jsonified:
		if not(os.path.isfile(str("export/" + t['key'] + ".html"))):
			f = open(("./export/" + t['key'] + ".html"), "w+")
			f.write(getEvent(getTeamsAtEvent(t['key']), t['key']))
			print("Updating " + t['key'].upper() + " via cache view.")
			f.close()
		elif (open("./export/" + t['key'] + ".html").read() == ""):
			f = open(("./export/" + t['key'] + ".html"), "w+")
			f.write(getEvent(getTeamsAtEvent(t['key']), t['key']))
			print("Updating " + t['key'].upper() + " via cache view.")
			f.close()

def statsTest():
	finalOut = "<link href=\"https://fonts.googleapis.com/css?family=Droid+Sans\" rel=\"stylesheet\"><link href=\"https://fonts.googleapis.com/css?family=Righteous\" rel=\"stylesheet\"> <style>body{font-family:'Droid Sans';}h1,h3{font-family:'Righteous';line-height: 70%;}.center{margin: auto;width: 60%;border:5px solid #ff6600;padding:10px;border-radius:10px;}</style>"
	finalOut+="<h4>" + tbaIncGet()  +" requests to The Blue Alliance and counting!</h4>"
	finalOut+="<h4>" + str(file_len("./flaskapp.py")) + " lines of code in this project.</h4>"
	finalOut+="<form action=\"admin/save/\" method=\"post\"><button name=\"foo\" value=\"upvote\">Save Entire Site to Static</button></form>"

	return finalOut
	

app = Flask(__name__)

@app.route('/')
def getEvents():
    return frontPage()

#Event is LIVE
@app.route('/event/<event>')
def scoutatevent(event):
    return getEvent(getTeamsAtEvent(event),event)

#Events is STATIC
@app.route('/events/<event>')
def scoutatevents(event):
    f = open(("./export/" + event + ".html"), "r")
    t = f.read()
    f.close()
    return t

#Stats Page
@app.route('/stats')
def simplestats():
    return statsTest()

#SAVE EVERYTHING
@app.route('/admin/save/', methods=['POST'])
def saveEvents():
    savePage()
    return ''

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)
