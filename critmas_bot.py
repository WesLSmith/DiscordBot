import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import urllib
import urllib.request
import requests
import re
import json
from random import randint

client = discord.Client()

description = "Bot for Newt3 Discord Server"
bot = commands.Bot(command_prefix = '?', description = description)

@bot.event
async def on_ready():
    print("logging in")
    print(bot.user.name)
    print("")


@bot.command()
async def info(command = None):
    if command:
        return #ADD A function to look at a specific function here
    await bot.say("Hello, I am a bot! These are some things I can do:\n"
        "?items champion lane \n"
        "       -Gets the three most popular build paths for the specified champion and lane. \n"
        "?counters champion lane \n"
        "       -Gets the five champions with the highest winrate versus the specified champion and lane. \n"
        "?bans\n"
        "       -Gets the five champs with the highest win rates this patch. \n"
        "----------------------------------------------------------------- \n"
        "Example: ?items Jhin Bot \n"
        "Example: ?counters Gnar Top \n"
        "Example: ?bans")

##Get Reccommended Items for Champion
@bot.command()
async def items(champion, lane=None):
    #Check if valid champion
    if not await get_champion_info(champion, message=True):
        return
    #Get most popular lane if needed
    if not lane:
        lane = await get_most_popular_lane(champion, message=True)
    htmldoc = urllib.request.urlopen("http://na.op.gg/champion/" + champion + "/statistics/" + lane + "/item").read()
    soup = BeautifulSoup(htmldoc)
    ##Get item names
    name_divs = soup.findAll("ul", {"class" : "champion-stats__list"})
    items = re.findall(r"bc'&gt;(.*?)&lt;", str(name_divs))
    ##Get Win Rates
    win_rate_divs = soup.findAll('td', {"class" :"champion-stats__table__cell--winrate"})
    win_rates = []

    for i in win_rate_divs:
        win_rates.append(str(i)[-11:-5])

    say_message = ""
    for i in range(0,8,3):
        say_message += ("Build {}: {} > {} > {} | Win Rate: {}\n".format(i//3 + 1, items[i], items[i+1], items[i+2], win_rates[i//3] ))
    await bot.say(say_message)

@bot.command()
async def picks(lane=None):
    #Get proper lane name
    if lane:
        proper_lane_name = await get_proper_lane_name(lane)
        if not proper_lane_name:
            await bot.say('{} is not a valid lane name. Please try again.'.format(lane))
            return
    #Get winrate page from champion.gg
    response = requests.get('http://champion.gg/statistics/#?sortBy=general.winPercent&order=descend')
    #Pull winrate table from the page
    exp = re.compile('matchupData.stats = \[[\S\s]*?\]')
    raw_string = exp.search(response.text).group(0)
    string = raw_string.replace('matchupData.stats = ', '')
    champion_list = json.loads(string)
    #If lane requested, filter accordingly
    if lane:
        champion_list = [champion for champion in champion_list if champion['role'] == proper_lane_name]
    champion_list.sort(key=lambda champion: champion['general']['winPercent'], reverse=True)
    #Output the top 5 -- wow those are some good picks!
    lane_output = ''
    if lane:
        lane_output = ' for {}'.format(proper_lane_name)
    output = 'According to champion.gg, some good picks{} are: {}, {}, {}, {}, and {}.'.format(lane_output, champion_list[0]['key'], champion_list[1]['key'], champion_list[2]['key'], champion_list[3]['key'], champion_list[4]['key'])
    await bot.say(output)

@bot.command()
async def bans():
    #Get winrate page from champion.gg
    response = requests.get('http://champion.gg/statistics/#?sortBy=general.winPercent&order=descend')
    #Pull winrate table from the page
    exp = re.compile('matchupData.stats = \[[\S\s]*?\]')
    raw_string = exp.search(response.text).group(0)
    string = raw_string.replace('matchupData.stats = ', '')
    champion_list = json.loads(string)
    champion_list.sort(key=lambda champion: champion['general']['winPercent'], reverse=True)
    #Output the top 5 -- wow those are some good bans!
    output = 'According to champion.gg, some good bans are: {}, {}, {}, {}, and {}.'.format(champion_list[0]['key'], champion_list[1]['key'], champion_list[2]['key'], champion_list[3]['key'], champion_list[4]['key'])
    if randint(0,100) == 44:
        output = 'According to the Grand Carnivalist, some good bans are: RIVEN, RIVEN, RIVEN, RIVEN, and RIVEN!'
    await bot.say(output)

##Get the top 5 counters for a given champion
@bot.command()
async def counters(champion, lane=None):
    #Get info
    info = await get_champion_info(champion, message=True)
    #Check if valid champion
    if not info:
        return
    #Get most popular lane if needed
    if not lane:
        lane = await get_most_popular_lane(champion, message=True)
    #Get best counters
    lane_name = await get_proper_lane_name(lane)
    top_5 = info['Matchups'][lane_name][:5]
    #Output
    say_message = ""
    for counter in top_5:
        say_message += ('{} wins {:.0f}% of the time ({} games)\n'.format(counter['Name'], counter['Win Rate']*100, counter['Games']))
    await bot.say(say_message)

#Returns a dictionary with some info about a given champion, or returns false and prints a message if the champion requested is invalid.
#This should help with further command development.
async def get_champion_info(champion, message=False):
    #Get champion's name in proper form
    champion_name = champion[:1].upper() + champion[1:].lower()
    #Get champion info page
    champion_response = requests.get('http://champion.gg/champion/{}'.format(champion_name))
    if champion_response.status_code == 500:
        if message:
            await bot.say('{} is not a valid champion name. Typo?'.format(champion))
        return False
    #Get lanes (in popularity order)
    lanes_exp = re.compile('\/champion\/{}\/[A-Za-z]*'.format(champion_name))
    raw_lanes_strings = lanes_exp.findall(champion_response.text)
    lanes = [raw_lane_string.replace('/champion/{}/'.format(champion_name), '') for raw_lane_string in raw_lanes_strings]
    #Get win rate
    win_rate_exp = re.compile('Win Rate\n      </a>\n     </td>\n     <td>\n      [0-9]*.[0-9]*%')
    raw_win_rate_string = win_rate_exp.search(champion_response.text).group(0)
    win_rate = raw_win_rate_string.replace('Win Rate\n      </a>\n     </td>\n     <td>\n      ', '')
    #Get matchups
    matchups = {}
    for lane in lanes:
        lane_response = requests.get('http://champion.gg/champion/{}/{}'.format(champion, lane))
        matchups_exp = re.compile('"matchups":\[[\s\S]*?]')
        raw_lane_matchups_string = matchups_exp.search(lane_response.text).group(0)
        lane_matchups_string = raw_lane_matchups_string.replace('"matchups":', '')
        lane_matchups_dict = json.loads(lane_matchups_string)
        lane_matchups_list = [{'Name': matchup['key'], 'Win Rate': 1 - matchup['winRate'], 'Games': matchup['games']} for matchup in lane_matchups_dict]
        lane_matchups_list.sort(key=lambda matchup: matchup['Win Rate'], reverse=True)
        matchups[lane] = lane_matchups_list
    #Return dictionary
    return {
        'Name': champion_name,
        'Lanes': lanes,
        'Win Rate': win_rate,
        'Matchups': matchups
    }

async def get_most_popular_lane(champion, message=False):
    info = await get_champion_info(champion)
    champion_name = info['Name']
    lane = info['Lanes'][0]
    if message:
        bot.say('No lane selected. Defaulting to {}\'s most popular lane, {}. ' \
            'If you want another lane, try something like this: "?items {} {}"'.format(champion_name, lane, champion_name, lane))
    return lane

async def get_proper_lane_name(lane):
    lane_name = lane.lower()
    lane_dict = {
                'jg': 'Jungle', 'jungle': 'Jungle', 'jungler': 'Jungle', 'j': 'Jungle',
                'top': 'Top', 't': 'Top',
                'mid': 'Middle', 'middle': 'Middle', 'm': 'Middle',
                'bot': 'ADC', 'adc': 'ADC', 'adcarry': 'ADC', 'b': 'ADC', 'a': 'ADC',
                'support': 'Support', 'supporter': 'Support', 'shitter': 'Support', 's': 'Support',
    }
    if lane_name not in lane_dict:
        return False
    return lane_dict[lane_name]

bot.run("Mzk0MjcxMjIxNjc3Njg2Nzk0.DSxz6A.Rj5IaLDsiEPwMQ2nX1GW6XL7_ZY")
