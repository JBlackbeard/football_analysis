import numpy as np
import pandas as pd
import math
from datetime import datetime


#ToDo: Merge with other dataset to get Match Day
#ToDo: seperate table with ELO scores #DONE
#ToDo: Get official play-by-plays







# import Premier League Data from season 18/19
dateparse = lambda x: pd.datetime.strptime(x, '%d/%m/%Y') # define date format for pd read_csv
df = pd.read_csv("/Users/jjs/Dropbox/Programming/football_gambling/PL_1819.csv", parse_dates=['Date'],date_parser=dateparse)
df.Date = pd.to_datetime(df.Date,unit='d') # convert from timestamp to datetime
df.index = df.Date # define the date as the index

# make sure the data is sorted by Date in ascending order
df.sort_index(ascending=True)

# Get all PL teams in order of their first match day
teams = [x for sub in list(zip(df['HomeTeam'][:10],df['AwayTeam'][:10])) for x in sub]

# define DataFrame 'elo' initialized with some elo initialization value and the date the team played first this season
elo_start_value = 500
elo = pd.DataFrame({'Team': teams, 'ELO': len(teams)*[elo_start_value]}, index=20*[datetime.strptime('01-01-2000', '%d-%m-%Y')])
elo.index.name = 'Date'




df.columns


# aggregate the odds from different oddsmakers with their median value
home_odds_cols = ['B365H','BWH','IWH', 'PSH', 'WHH', 'VCH','PSCH']
away_odds_cols = ['B365A','BWA','IWA', 'PSA', 'WHA', 'VCA','PSCA']
draw_odds_cols = ['B365D','BWD','IWD', 'PSD', 'WHD', 'VCD','PSCD']

df['home_odds'] = df.loc[:,home_odds_cols].median(axis=1)
df['draw_odds'] = df.loc[:,draw_odds_cols].median(axis=1)
df['away_odds'] = df.loc[:,away_odds_cols].median(axis=1)

cols_to_drop = home_odds_cols + away_odds_cols + draw_odds_cols + ['Div','Bb1X2','BbAH','BbAHh', 'BbMxH','BbMxD','BbMxA','BbMx>2.5','BbMx<2.5','BbMxAHH','BbMxAHA','BbAvH','BbAvD','BbAvA','BbAv>2.5','BbAv<2.5','BbAvAHH','BbAvAHA','BbOU','Referee' ]



df = df.drop(cols_to_drop, axis=1)

# ELO RATING SYSTEM

def Probability(rating1, rating2):
    """
    Based on the elo Rating of both teams the win probability is calculated
    """
    return 1.0 * 1.0 / (1 + 1.0 * math.pow(10, 1.0 * (rating1 - rating2) / 400))

def EloRating(homeElo, awayElo, outcome, k=30):
    """
    Recalculates elo Ratings for both teams and returns both values
    
    Keyword arguments: 
    homeElo -- current elo rating home team
    awayElo -- current elo rating away team
    K -- weight for elo calculation
    outcome -- 'H','D','A' for home, draw and away result respectively
    
    """
    # calculate winning probability of home and away team
    Ph = Probability(awayElo, homeElo)
    Pa = Probability(homeElo, awayElo)
    
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


for index,row in df.loc[:,['Date','HomeTeam','AwayTeam','FTR']].iterrows():
    eloHome = elo.loc[(elo.Team == row[1]) & (elo.index == elo.loc[(elo.Team == row[1])].index.max())].ELO[0]
    eloAway = elo.loc[(elo.Team == row[2]) & (elo.index == elo.loc[(elo.Team == row[2])].index.max())].ELO[0]
    eloHome, eloAway = EloRating(eloHome, eloAway, row[3])
    elo = elo.append(pd.DataFrame({'Team': [row[1], row[2]], 'ELO': [eloHome,eloAway]}, index=2*[row[0]]))


    