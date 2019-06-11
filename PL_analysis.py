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
            
            
        df_new['season'] = df_new.Date.max().year # add season column, defined as the year of the last matchday
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
#csv_files = [wd + "/PL_1617.csv"]



#df = pd.read_csv("/Users/jjs/Dropbox/Programming/football_gambling/PL_1819.csv", parse_dates=['Date'],date_parser=dateparse, delimiter=';')
df = merge_data(csv_files)
df.Date = pd.to_datetime(df.Date,unit='d') # convert from timestamp to datetime

# make sure the data is sorted by Date in ascending order
df.sort_index(ascending=True)

# Get all PL teams in order of their first match day
#teams = [x for sub in list(zip(df['HomeTeam'][:10],df['AwayTeam'][:10])) for x in sub]
teams = df.HomeTeam.unique()

# define DataFrame 'elo' initialized with some elo initialization value and the date the team played first this season
elo_start_value = 1000
teamData = pd.DataFrame({'Team': teams,
                         'goals_scored': len(teams) * [0],
                         'goals_conceded': len(teams) * [0],
                         'matchDay': len(teams) * [0],
                         'points': len(teams) * [0],
                         'avg_points_game': len(teams) * [0],
                         'season': len(teams) * [0],
                         'ELO': len(teams)*[elo_start_value],
                        'Date':len(teams)*[datetime.strptime('01-01-2000', '%d-%m-%Y')]
})



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


trend_length = 5

points_mapping_home = {'H': 3, 'D': 1, 'A': 0} # resulting points for each possible game result
points_mapping_away = {'H': 0, 'D': 1, 'A': 3}
for index,row in df.loc[:,['Date','HomeTeam','AwayTeam','FTR','FTHG','FTAG','matchDay', 'first_match_day', 'season']].iterrows():
    matching_teamData_home = teamData.loc[(teamData.Team == row[1]) & (teamData.Date == teamData.loc[(teamData.Team == row[1])].Date.max())]
    matching_teamData_away = teamData.loc[(teamData.Team == row[2]) & (teamData.Date == teamData.loc[(teamData.Team == row[2])].Date.max())]

    eloHome = matching_teamData_home.ELO.item()
    eloAway = matching_teamData_away.ELO.item()
    home_goals = matching_teamData_home.goals_scored.item()
    home_conceded = matching_teamData_home.goals_conceded.item()
    away_goals = matching_teamData_away.goals_scored.item()
    away_conceded = matching_teamData_away.goals_conceded.item()
    matchday_home = matching_teamData_home.matchDay.item()
    matchday_away = matching_teamData_away.matchDay.item()
    home_points_old = matching_teamData_home.points.item()
    away_points_old = matching_teamData_away.points.item()
    home_result = row[3] # 'H', 'D' or 'A' for Home win, Draw and Away win
    home_points_new = points_mapping_home[home_result]
    away_points_new = points_mapping_away[home_result]
    if row[7] == True: # if it's the first match day, adjust elo ratings
        eloHome = 0.9 * eloHome + 0.1 * elo_start_value
        eloAway = 0.9 * eloHome + 0.1 * elo_start_value
        home_goals = 0
        home_conceded = 0
        away_goals = 0
        away_conceded = 0
        matchday_home = 0
        matchday_away = 0
        #home_points_new = 0
        home_points_old = 0
        #away_points_new = 0
        away_points_old = 0
        teamData = teamData.append(pd.DataFrame({'Team': [row[1], row[2]],
                                                 'goals_scored':0,
                                                 'goals_conceded':0,
                                                 'ELO': [eloHome,eloAway],
                                                 'matchDay':[0, 0],
                                                 'avg_goals_scored': [0,0],
                                                 'avg_goals_conceded': [0,0],
                                                 'points': [0,0],
                                                 'season': row[8],
                                                 'avg_points_game': [0,0],
                                                 'elo_change_trend': [np.NaN, np.NaN],
                                                 'goals_scored_trend': [np.NaN, np.NaN],
                                                 'goals_conceded_trend': [np.NaN, np.NaN],
                                                'Date':2*[row[0]-timedelta(days=14)]
                                                }))
                                                




    
    goalDiff = abs(row[4] - row[5])
    eloHome, eloAway = EloRating(eloHome, eloAway, row[3], k=20 + goalDiff**2)
    teamData = teamData.append(pd.DataFrame({'Team': [row[1], row[2]],
                                             'goals_scored': [home_goals+row[4], away_goals+row[5]],
                                             'goals_conceded': [home_conceded+row[5], away_conceded+row[4]],
                                             'ELO': [eloHome,eloAway],
                                             'matchDay': [matchday_home+1, matchday_away+1],
                                             'avg_goals_scored': [round((home_goals+row[4])/(matchday_home+1),3), round((away_goals+row[5])/(matchday_away+1),3)],
                                             'avg_goals_conceded': [round((home_conceded+row[5])/(matchday_home+1),3), round((away_conceded+row[4])/(matchday_away+1),3)],
                                             'points': [home_points_old + home_points_new, away_points_old + away_points_new],
                                             'avg_points_game': [round((home_points_old + home_points_new)/(matchday_home+1),3), round((away_points_old + away_points_new)/(matchday_away+1),3)],
                                             'season': row[8],
                                             'elo_change_trend': [np.NaN, np.NaN],
                                             'goals_scored_trend': [np.NaN, np.NaN],
                                             'goals_conceded_trend': [np.NaN, np.NaN],
                                             'Date':2*[row[0]], 
                                             
                                            }
                                            
                                           ,index = [len(teamData)-2, len(teamData)-1]
                                           
                                           ))
                                            
    



    
    
    if matchday_home > trend_length:
        home_team_season = teamData.loc[(teamData.Team == row[1]) & (teamData.season == row[8])]
    
        eloChange_home =  round(home_team_season.loc[home_team_season.matchDay == matchday_home+1].ELO.item()
                                - home_team_season.loc[home_team_season.matchDay == matchday_home+1-trend_length+1].ELO.item(),2)
        
        goals_scored_trend_home = round((home_team_season.loc[home_team_season.matchDay == matchday_home+1].goals_scored.item()
                                - home_team_season.loc[home_team_season.matchDay == matchday_home+1-trend_length+1].goals_scored.item())/trend_length,2)
        
        goals_conceded_trend_home = round((home_team_season.loc[home_team_season.matchDay == matchday_home+1].goals_conceded.item()
                                - home_team_season.loc[home_team_season.matchDay == matchday_home+1-trend_length+1].goals_conceded.item())/trend_length,2)
        
        teamData.at[teamData.index[-2], 'elo_change_trend'] = eloChange_home
        teamData.at[teamData.index[-2], 'goals_scored_trend'] = goals_scored_trend_home
        teamData.at[teamData.index[-2], 'goals_conceded_trend'] = goals_conceded_trend_home


        
    if matchday_away > trend_length:
        away_team_season = teamData.loc[(teamData.Team == row[2]) & (teamData.season == row[8])]
        
        eloChange_away =  round(away_team_season.loc[away_team_season.matchDay == matchday_away+1].ELO.item()
                                - away_team_season.loc[away_team_season.matchDay == matchday_away+1-trend_length+1].ELO.item(),2)
        
        goals_scored_trend_away = round((away_team_season.loc[away_team_season.matchDay == matchday_away+1].goals_scored.item()
                                - away_team_season.loc[away_team_season.matchDay == matchday_away+1-trend_length+1].goals_scored.item())/trend_length,2)
        
        goals_conceded_trend_away = round((away_team_season.loc[away_team_season.matchDay == matchday_away+1].goals_conceded.item()
                                - away_team_season.loc[away_team_season.matchDay == matchday_away+1-trend_length+1].goals_conceded.item())/trend_length,2)
        
        teamData.at[teamData.index[-1], 'elo_change_trend'] = eloChange_away
        teamData.at[teamData.index[-1], 'goals_scored_trend'] = goals_scored_trend_away
        teamData.at[teamData.index[-1], 'goals_conceded_trend'] = goals_conceded_trend_away





