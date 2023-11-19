import json
import pandas as pd
import cmath
import xml.etree.ElementTree as et
import numpy as np
from datetime import timedelta

shotlist = ['Shot into the bar/post',
'Blocked shot',
'Shots blocked',
'Shot on target',
'Chance was not converted by',
'Wide shot',
'Shot blocked by field player',
'Chance was converted by',
'Accurate crossing from set piece with a shot',
'Misplaced crossing from set piece with a shot',
'Accurate crossing from set piece with a goal',
'Set piece cross with goal',
'Goal'
]

ontarget= [
    'Shot on target',
    'Goal'
]


def standart_transform(standart):
    match standart:
        case 'Indirect free kick':
            return "free_kick"
        case 'Goal kick':
            return "goal_kick"
        case 'Corner':
            return "corner"
        case 'Throw-in':
            return "throw-in"
        case 'Direct free kick':
            return "free_kick"
        case 'Penalty':
            return "penalty"
        case _:
            raise Exception("something went wrong in standart transform")

def position_transform(instat_position, formation):
    defenders=formation[0]
    midfielders = formation[2]
    match instat_position:
        case 'Goalkeeper':
            return "GK"
        case 'Defender - Central':
            return "CB"
        case 'Defender - Left central':
            if (defenders==4):
                return "LCB"
            return "LCB3"
        case 'Defender - Right central':
            if (defenders==4):
                return "RCB"
            return "RCB3"
        case 'Defender - Right':
            if (defenders==5):
                return "RB5"
            return "RB"
        case 'Defender - Left':
            if (defenders==5):
                return "LB5"
            return "LB"
        case 'Defensive midfielder - Right central':
            return "RDMF"
        case 'Defensive midfielder - Left central':
            return "LDMF"
        case 'Defensive midfielder - Central':
            return "DMF"
        case 'Midfielder - Right central':
            if(midfielders==3 or midfielders==5):
                return "RCMF3"
            return "RCMF"
        case 'Midfielder - Left central':
            if(midfielders==3 or midfielders==5):
                return "LCMF3"
            return "LCMF"
        case 'Midfielder - Right':
            return "RW"
        case 'Midfielder - Left':
            return "LW"
        case 'Attacking midfielder - Right central':
            return "RAMF"
        case 'Attacking midfielder - Left central':
            return "LAMF"
        case 'Attacking midfielder - Right':
            return "RWF"
        case 'Attacking midfielder - Left':
            return "LWF"
        case 'Attacking midfielder - Central':
            return "AMF"
        case 'Forward - Right central':
            return "SS"
        case 'Forward - Left central':
            return "CF"
        case 'Forward - Central':
            return "CF"
        case None:
            return None
        case _:
            print(instat_position)
            raise Exception("position could not be found")
        

#subfunctions



def get_possession_type(df, ind, list):
    t = df['standart_name'].iloc[ind]
    t2 = df['attack_type_name'].iloc[ind]
    match t:
        case "Direct free kick":
            list+=["direct_free_kick"]
        case "Corner":
            list+=["corner"]
        case "Throw-in":
            list+=["throw-in"]
        case "Penalty":
            list+=["penalty"]
 
    match t2:
        case "Counter-attack":
            list+=["counterattack", "attack"]
        case None:
            return list
        case _:
            list+=["attack"]
    return list

def get_possession_attack(df, ind, withshot, withshotongoal, goal, flank):
    t2 = df['attack_type_name'].iloc[ind]
    action = df['action_name'].iloc[ind]
    flang = df['attack_flang_name'].iloc[ind]
    
    match t2:
        case None:
            return withshot, withshotongoal, goal, flank
        case _:
            if(np.isnan(withshot)):
                withshot=withshotongoal=goal=False
                flank = flang
                return withshot, withshotongoal, goal, flank
            else:
                if (action in shotlist):
                    withshot=True
                if(action in ontarget):
                    withshotongoal=True
                if(action=='Goal'):
                    goal=True
                flank = flang
                return withshot, withshotongoal, goal, flank
            


def time_transform(sec):
    t=timedelta(seconds=sec)
    if(t.microseconds>0):
       return str(t)[:-3] 
    return str(t)+'.000'



def get_formation(team, formationlist, teamlist):
    if (team==teamlist[0]):
        return formationlist[0]
    return formationlist[1]


def location_transform(x,y):
    new_x = x*100/105
    new_y = y*-100/68+100
    return new_x,new_y
    

#attribute functions

def get_period(df, index):
    per = df['half'].iloc[index]
    if (per==1):
        return "1H"
    return "2H"

def get_time(df, index):
    sec = df['second'].iloc[index]
    min = int(sec/60)
    second = int(sec%60)
    return min, second, time_transform(sec)

def get_location(df, index):
    locx = df["pos_x005F_x"].iloc[index]
    locy = df["pos_y"].iloc[index]
    return location_transform(locx, locy)





def setnewpossession(df, index):
    poss_types=[]
    withshot=withshotongoal= withgoal=flank=np.nan
    
    if(df['action_name'].iloc[index]=='Match end'):
        return [0,0,0,0,0,index], poss_types, withshot, withshotongoal, withgoal, flank
    
    length = df['possession_time'].iloc[index]
    while (np.isnan(length)):
        index+=1
        if(df['action_name'].iloc[index]=='Match end'):
            return [0,0,0,0,0,index], poss_types, withshot, withshotongoal, withgoal, flank
        length = df['possession_time'].iloc[index]

    
    if (length==0):
        startx, starty = get_location(df, index)
        i = index
        poss_types=get_possession_type(df, index, poss_types)
        withshot, withshotongoal, withgoal, flank = get_possession_attack(df, index, withshot, withshotongoal, withgoal, flank)

    else: 
        raise Exception("possession could not been set")

    while (np.isnan(length) or length==0):
        index+=1
        if(df['action_name'].iloc[index]=='Match end'):
            return [0,0,0,0,0,index], poss_types, withshot,withshotongoal, withgoal, flank
        length = df['possession_time'].iloc[index]
        poss_types=get_possession_type(df, index, poss_types)
        withshot,withshotongoal, withgoal, flank = get_possession_attack(df, index, withshot, withshotongoal, withgoal, flank)

    endx, endy = get_location(df,index)
    return [startx, starty, endx, endy, length, i], list(set(poss_types)), withshot, withshotongoal, withgoal, flank


events=[
    'Match end', 
    'Clearance',
    'Offside',
    'Own goal',


]
standart_events=[
 'Indirect free kick',
 'Goal kick',
 'Corner',
 'Throw-in',
 'Direct free kick',
 'Penalty'
]

duel_events= [
    'Tackle',
    'Challenge',
    'Air challenge',
    'Successful dribbling',
    'Unsuccessful dribbling'
]
gameinterruption_events=[
    'Deferred foul',
    'Red card',
    'Foul',
    'Yellow card',
    'RC for two YC'
]

infraction_events = [

]
interception_events = [

]

pass_events = [

]

shot_events = [

]

def get_primary_type (df, index):
    action = df['action_name'].iloc[index]
    standart = df['standart_name'].iloc[index]
    if standart in standart_events:
        if (index>0):
            return standart_transform(standart)
    if action =='Clearance':
        return "clearance"
    if action in duel_events:
        return "duel"
    if action in gameinterruption_events:
        return "game_interruption"
    if action in infraction_events:
        return "infraction"
    if action in interception_events:
        return "interception"
    if action == 'Offside':
        return "offside"
    if action == 'Own goal':
        return "own_goal"
    if action in pass_events:
        return "pass"
    if action in shot_events:
        return "shot"
    if action == "Dribbling":
        "touch"

def get_secondary_type(df, index, l):
    return [] #to do


def get_event_type(df, index):
    secondary=[]
    action = df['action_name'].iloc[index]
    standart = df['standart_name'].iloc[index]
    if (action=='Match end'):
        raise Exception ("event match end should not been reached in this state")
    primary = get_primary_type(df, index)
    index+=1
    while(action not in events):  #have to check penalties
        secondary = get_secondary_type(df, index, secondary)
        index+=1
        action=df['action_name'].iloc[index]
    return index, primary, secondary
