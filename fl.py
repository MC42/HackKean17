#!/usr/bin/python3
from flask import Flask, render_template
import requests
import sqlite3
import sys
import datetime
import os.path

global tbaRequests
tbaRequests = 0

year = str(datetime.datetime.today().year)
bestWorst = 4

baseURL = 'http://www.thebluealliance.com/api/v2/'
header = {'X-TBA-App-Id': 'tjf:particleprescouter:hackkean3'} #Yay, version strings....

conn = sqlite3.connect(':memory:',detect_types=sqlite3.PARSE_DECLTYPES| sqlite3.PARSE_COLNAMES, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('CREATE TABLE `MATCHES` (	`KEY`	TEXT,	`SCORE`	INTEGER);')

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
	tbaRequests+=1

def getEvent(teams, eventCode):
	tbaIncrement()
	finalOut ="<link href=\"https://fonts.googleapis.com/css?family=Droid+Sans|Righteous\" rel=\"stylesheet\"><style>table{font-size:14px;}th{text-align:left;}	.center{margin: auto;    border: 3px solid #ff6600;    padding: 10px;border-radius:10px;}body{font-family:'Droid Sans';}h1,h3{font-family:'Righteous';line-height: 70%;}</style>"
	finalOut += "<h1 style=\"text-align:center\">" + eventCode.upper() + " Event</h1>"
	finalOut += "<table class=\"center\" style=\"width:100%;\">"
	finalOut+="<tr><th>Team No.</th>"
	for num in range(bestWorst):
		finalOut+="<th>#" + str(num+1) + " Best Match</th>"
	for num in reversed(range(bestWorst)):
		finalOut+="<th>#" + str(num+1) + " Worst Match</th>"

	finalOut+="</tr>"
	for i in teams:	
		tbaIncrement()
		myRequest = (baseURL + 'team/frc'+ str(i) + '/2017/events')
		response = requests.get(myRequest, headers=header)
		jsonified = response.json()

		for thing in jsonified:
			getTeamMatchesAtEvent(i, str(thing['key']))
		cursor.execute('SELECT * FROM MATCHES ORDER BY SCORE DESC LIMIT ?;', (bestWorst,))
		bestMatches = cursor.fetchall()	
		finalOut+="<tr>"
		finalOut+="<td><a href=\"" + tbaTeam(i) + "\">" + str(i) + "</td>"
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

	f = open(("./export/" + eventCode + ".html"), "w+")
	f.write(finalOut)
	print("Updating " + eventCode.upper() + " via non-static view.")
	f.close()
	return finalOut

def frontPage():
	# <a href="https://www.w3schools.com">Visit W3Schools</a> 
	finalOut = "<link href=\"https://fonts.googleapis.com/css?family=Droid+Sans\" rel=\"stylesheet\"><link href=\"https://fonts.googleapis.com/css?family=Righteous\" rel=\"stylesheet\"> <style>body{font-family:'Droid Sans';}h1,h3{font-family:'Righteous';line-height: 70%;}</style>"	
	finalOut += "<style>.center{margin: auto;width: 60%;border:5px solid #ff6600;padding:10px;border-radius:10px;}</style>"
	myRequest = (baseURL + "events/"+ str(year))
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	jsonified.sort(key=lambda r: r['end_date'])
	finalOut+="<h1 style=\"text-align:center\">Particle Prescouter</h1><h3 style=\"text-align:center\">FIRST Robotics Competition</h3>"
	finalOut+="<div class=\"center\"><table style=\"width:100%;\">"
	finalOut+="<tr><th>Week No.</th><th>Event Short Name</th><th>Event Location</th></tr>"
	for t in jsonified:
		finalOut+="<tr><td>"+ str(t['week'])+ "</td><td><a href=\"events/" + t['key'] + "\">" + t['short_name'] + " (" + t['event_code'].upper() + ")</a></td><td>" + t['location'] + "</td></tr>"
	finalOut+="</table>"
	finalOut+="<h6 style=\"text-align:center\">40k+ Requests (And Counting!)</h6></div>"
	return finalOut

def savePage():
	myRequest = (baseURL + "events/"+ str(year))
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	for t in jsonified:
		if not(os.path.isfile(str("export/" + t['key'] + ".html"))):
			f = open(("./export/" + t['key'] + ".html"), "w+")
			f.write(getEvent(getTeamsAtEvent(t['key']), t['key']))
			print("Updating " + t['key'].upper() + " via cache view.")
			f.close()

app = Flask(__name__)

@app.route('/event/<event>')
def scoutatevent(event):
    return getEvent(getTeamsAtEvent(event),event)

@app.route('/events/<event>')
def scoutatevents(event):
    f = open(("./export/" + event + ".html"), "r")
    t = f.read()
    f.close()
    return t


@app.route('/')
def getEvents():
    return frontPage()

@app.route('/save')
def saveEvents():
    savePage()
    return "Saved!"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)




