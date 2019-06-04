import numpy as np
import pandas as pd
import math
from datetime import datetime
from datetime import timedelta
#https://www.nytimes.com/2019/05/22/magazine/soccer-data-liverpool.html?utm_campaign=Data_Elixir&utm_medium=email&utm_source=Data_Elixir_235

#ToDo: Merge with other dataset to get Match Day
#ToDo: seperate table with ELO scores # Done
#ToDo: Get official play-by-plays







# import Premier League Data from seasons 1617 to 1819
dateparse = lambda x: pd.datetime.strptime(x, '%d/%m/%Y') # define date format for pd read_csv

def merge_data(csv_files, delimiter = ',', dateparser = dateparse, parse_dates = ['Date']):
    """
    merges data from different csv files for different seasons
    
    Keyword arguments: 
    csv_files -- list with csv file locations
    delimiter -- delimiter for csv format
    dateparser -- format for pd.read_csv function for dates
    parse_date -- specify date column 
    
    """
    
    for csv in csv_files:
        try:
            df_new = pd.read_csv(csv, parse_dates=parse_dates ,date_parser=dateparser, delimiter=delimiter)
        except:
            df_new = pd.read_csv(csv, parse_dates=parse_dates ,date_parser=lambda x: pd.datetime.strptime(x, '%d/%m/%y'), delimiter=delimiter)
            
            
        df_new["season"] = df_new.Date.max().year # add season column, defined as the year of the last matchday
        df_new['first_match_day'] = False 
        df_new['first_match_day'][0:10] = True
        df_new['matchDay'] = 0
        #df_new['matchDay'][0:10] = 1
        
        try:
            df = df.append(df_new,sort=False)
        except:
            df = df_new
        
    return df
wd = "/Users/jjs/Dropbox/Programming/football_gambling/"
csv_files = [wd + "PL_1617.csv", wd + "PL_1718.csv", wd + "/PL_1819.csv"]
#df = pd.read_csv("/Users/jjs/Dropbox/Programming/football_gambling/PL_1819.csv", parse_dates=['Date'],date_parser=dateparse, delimiter=';')
df = merge_data(csv_files)
df.Date = pd.to_datetime(df.Date,unit='d') # convert from timestamp to datetime
df.index = df.Date # define the date as the index

# make sure the data is sorted by Date in ascending order
df.sort_index(ascending=True)

# Get all PL teams in order of their first match day
#teams = [x for sub in list(zip(df['HomeTeam'][:10],df['AwayTeam'][:10])) for x in sub]
teams = df.HomeTeam.unique()

# define DataFrame 'elo' initialized with some elo initialization value and the date the team played first this season
elo_start_value = 1000
teamData = pd.DataFrame({'Team': teams, 'goals_scored': len(teams) * [0], 'goals_conceded': len(teams) * [0], 'matchDay': len(teams) * [0], 'ELO': len(teams)*[elo_start_value]}, index=len(teams)*[datetime.strptime('01-01-2000', '%d-%m-%Y')])
teamData.index.name = 'Date'



# aggregate the odds from different oddsmakers with their median value
home_odds_cols = ['B365H','BWH','IWH', 'PSH', 'WHH', 'VCH','PSCH']
away_odds_cols = ['B365A','BWA','IWA', 'PSA', 'WHA', 'VCA','PSCA']
draw_odds_cols = ['B365D','BWD','IWD', 'PSD', 'WHD', 'VCD','PSCD']

df['home_odds'] = df.loc[:,home_odds_cols].median(axis=1)
df['draw_odds'] = df.loc[:,draw_odds_cols].median(axis=1)
df['away_odds'] = df.loc[:,away_odds_cols].median(axis=1)

cols_to_drop = home_odds_cols + away_odds_cols + draw_odds_cols + ['Div','Bb1X2','BbAH','BbAHh', 'BbMxH','BbMxD','BbMxA',
                                                                   'BbMx>2.5','BbMx<2.5','BbMxAHH','BbMxAHA','BbAvH','BbAvD',
                                                                   'BbAvA','BbAv>2.5','BbAv<2.5','BbAvAHH','BbAvAHA','BbOU','Referee', 'LBH','LBD','LBA' ]



df = df.drop(cols_to_drop, axis=1)


# ELO RATING SYSTEM

def Probability(rating1, rating2):
    """
    Based on the elo Rating of both teams the win probability is calculated
    """
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

def EloRating(homeElo, awayElo, outcome, k=20):
    """
    Recalculates elo Ratings for both teams and returns both values
    
    Keyword arguments: 
    homeElo -- current elo rating home team
    awayElo -- current elo rating away team
    K -- weight for elo calculation
    outcome -- 'H','D','A' for home, draw and away result respectively
    
    """
    # calculate winning probability of home and away team
    Ph = Probability(awayElo*0.95, homeElo*1.05)
    Pa = Probability(homeElo*1.05, awayElo*0.95)
    
    # update Elo ratings according to outcome
    
    if (outcome == 'H'):
        homeElo = homeElo + k * (1 - Ph)
        awayElo = awayElo + k * (0 - Pa)
        
    if (outcome == 'D'):
        homeElo = homeElo + k * (0.5 - Ph)
        awayElo = awayElo + k * (0.5 - Pa)
        
    if (outcome == 'A'):
        homeElo = homeElo + k * (0 - Ph)
        awayElo = awayElo + k * (1 - Pa)
    
    return round(homeElo,2), round(awayElo,2)



for index,row in df.loc[:,['Date','HomeTeam','AwayTeam','FTR','FTHG','FTAG','matchDay', 'first_match_day']].iterrows():
    matching_teamData_home = teamData.loc[(teamData.Team == row[1]) & (teamData.index == teamData.loc[(teamData.Team == row[1])].index.max())]
    matching_teamData_away = teamData.loc[(teamData.Team == row[2]) & (teamData.index == teamData.loc[(teamData.Team == row[2])].index.max())]
    eloHome = matching_teamData_home.ELO[0]
    eloAway = matching_teamData_away.ELO[0]
    home_goals = matching_teamData_home.goals_scored[0]
    home_conceded = matching_teamData_home.goals_conceded[0]
    away_goals = matching_teamData_away.goals_scored[0]
    away_conceded = matching_teamData_away.goals_conceded[0]
    matchday_home = matching_teamData_home.matchDay[0]
    matchday_away = matching_teamData_away.matchDay[0]
    if row[7] == True: # if it's the first match day, adjust elo ratings
        eloHome = 0.75 * eloHome + 0.25 * elo_start_value
        eloAway = 0.75 * eloHome + 0.25 * elo_start_value
        home_goals = 0
        home_conceded = 0
        away_goals = 0
        away_conceded = 0
        matchday_home = 0
        matchday_away = 0
        teamData = teamData.append(pd.DataFrame({'Team': [row[1], row[2]], 'goals_scored':0,
                                                 'goals_conceded':0,
                                                 'ELO': [eloHome,eloAway],
                                                 'matchDay':[matchday_home, matchday_away],
                                                 'avg_goals_scored': [0,0],
                                                 'avg_goals_conceded': [0,0]
                                                
                                                },
                                                index=2*[row[0]-timedelta(days=14)]), sort=False)


    goalDiff = abs(row[4] - row[5])
    eloHome, eloAway = EloRating(eloHome, eloAway, row[3], k=20 + goalDiff**2)
    teamData = teamData.append(pd.DataFrame({'Team': [row[1], row[2]],
                                             'goals_scored': [home_goals+row[4], away_goals+row[5]],
                                             'goals_conceded': [home_conceded+row[5], away_conceded+row[4]],
                                             'ELO': [eloHome,eloAway],
                                             'matchDay': [matchday_home+1, matchday_away+1],
                                             'avg_goals_scored': [round((home_goals+row[4])/(matchday_home+1),3), round((away_goals+row[5])/(matchday_away+1),3)],
                                             'avg_goals_conceded': [round((home_conceded+row[5])/(matchday_home+1),3), round((away_conceded+row[4])/(matchday_away+1),3)]
                                            },
                                            index=2*[row[0]]),  sort=False)


    