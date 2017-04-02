#!/usr/bin/python3
import requests
import sqlite3
import sys
year = "2017"
bestWorst = 4

tbaCalls = 0

def incrementTBA():
	global tbaCalls
	tbaCalls+=1

# WRITTEN BY TIM FLYNN FOR TEAM 1257
# WRITTEN WITH LOVE <3

baseURL = 'http://www.thebluealliance.com/api/v2/'
header = {'X-TBA-App-Id': 'tjf:scoutingparticle:fm2'} #Yay, version strings....

#If you plan to use manually entered teams, define team here and comment out the team function at the bottom of this file.
#Otherwise format it as follows:
#teams = [11,193,1678,404]


def getDistricts(year):
	incrementTBA()
	myReq = (baseURL + "districts/" + year)
	resp = requests.get(myReq, headers=header)
	jsonif = resp.json()
	return jsonif

def getDistrictTeams(district):
	incrementTBA()
	myRequest = (baseURL + "district/"+ district + "/2017/teams")
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	teams = []
	for t in jsonified:
		teams.append(t['team_number'])
	teams = sorted(teams)
	return teams

conn = sqlite3.connect(':memory:',detect_types=sqlite3.PARSE_DECLTYPES| sqlite3.PARSE_COLNAMES)
cursor = conn.cursor()

cursor.execute('CREATE TABLE `MATCHES` (	`KEY`	TEXT,	`SCORE`	INTEGER);')

def getTeamName(i):
	incrementTBA()
	myRequest = (baseURL + 'team/frc'+ str(i) + '')
	response = requests.get(myRequest, headers=header)
	jsonified = response.json()
	return (jsonified['nickname'])

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
			

def getTeamsAtEvent(key):
	incrementTBA()
	myR = (baseURL + 'event/' + key + '/teams')
	re = requests.get(myR, headers=header)
	teams = re.json()
	teamList=[]
	for t in teams:
		teamList.append((t['team_number']))
	teamList = sorted(teamList)
	return teamList

def getTeamMatchesAtEvent(i, key):
	incrementTBA()
	myRequest = (baseURL + 'team/frc'+ str(i) + '/event/' + key + '/matches')
	response = requests.get(myRequest, headers=header)
	events = response.json()
	for match in events:
		matchLogic(match, i, key)

def theBeginning():
	matchKey=""
	#matchKey = "https://thebluealliance.com/match/"
	for i in teams:
		incrementTBA()
		myRequest = (baseURL + 'team/frc'+ str(i) + '/2017/events')
		response = requests.get(myRequest, headers=header)
		jsonified = response.json()

		for thing in jsonified:
			getTeamMatchesAtEvent(i, str(thing['key']))

		cursor.execute('SELECT * FROM MATCHES ORDER BY SCORE DESC LIMIT ?;', (bestWorst,))
		bestMatches = cursor.fetchall()		
		print(str(i) + "\t", end="")
		for gMatch in bestMatches:
			print(matchKey + gMatch[0] + "\t",end="")
		cursor.execute('SELECT * FROM MATCHES ORDER BY SCORE ASC LIMIT ?;', (bestWorst,))
		worstMatches = cursor.fetchall()
		for badMatch in worstMatches:
			print(matchKey + badMatch[0] + "\t", end="")
		if (len(worstMatches) == 0):
			print("No matches played yet, check back later.", end="")
		print("\t")

		cursor.execute("DELETE FROM MATCHES;")  #CLEANUP FOR NEXT TEAM


if len(sys.argv) > 1:
	teams = getTeamsAtEvent(str(sys.argv[1]))
#teams = getTeamsAtEvent("2017pahat")
theBeginning()
print(str(tbaCalls))
#And we're off to the races!

