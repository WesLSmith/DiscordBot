import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import urllib
import urllib.request
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

##Get Reccommended Items for Champion
@bot.command()
async def items(champion, lane = None):
    if lane is None:
        lane = get_most_popular_lane(champion, message=True)
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
    await bot.say("The top three %s %s builds are: (op.gg)" % (champion, lane))
    message1 = "Build 1: " + items[0] + " > " + items[1] + " > " + items[2] + " | Win Rate: " + win_rates[0]
    message2 = "Build 2: " + items[3] + " > " + items[4] + " > " + items[5] + " | Win Rate: " + win_rates[1]
    message3 = "Build 3: " + items[6] + " > " + items[7] + " > " + items[8] + " | Win Rate: " + win_rates[2]
    await bot.say(message1)
    await bot.say(message2)
    await bot.say(message3)

@bot.command()
async def bans():
    #Get winrate page from champion.gg
    htmldoc = urllib.request.urlopen('http://champion.gg/statistics/#?sortBy=general.winPercent&order=descend').read()
    soup = BeautifulSoup(htmldoc)
    data = str(soup.find_all('script')[18])

    #Pull winrate table from the page
    exp = re.compile('\[[A-Za-z0-9:.,"\}\{ -_]*\]')
    match = exp.search(data)
    champ_string = match.string[match.start():match.end()]
    champ_dict = json.loads(champ_string)

    #Construct simpler list (dictionaries containing name, winrate)
    champ_list = []
    for champ in champ_dict:
        name = champ['key']
        winrate = champ['general']['winPercent']
        champ_list.append({'name': name, 'winrate': winrate})
    champ_list.sort(key=lambda champ: champ['winrate'], reverse=True)

    #Output the top 5 -- wow those are some good bans!
    output = 'According to champion.gg, some good bans are: {}, {}, {}, {}, and {}.'.format(champ_list[0]['name'], champ_list[1]['name'], champ_list[2]['name'], champ_list[3]['name'], champ_list[4]['name'])
    meme_output = 'According to the Grand Carnivalist, some good bans are: RIVEN, RIVEN, RIVEN, RIVEN, and RIVEN!'
    if randint(0,100) == 44:
        await bot.say(meme_output)
    else:
        await bot.say(output)

##Get the top 5 counters for a given champion
@bot.command()
async def counters(champion, lane = None):
    if lane is None:
        lane = get_most_popular_lane(champion, message=True)
    htmldoc = urllib.request.urlopen("http://na.op.gg/champion/" + champion + "/statistics/" + lane + "/matchups").read()
    soup = BeautifulSoup(htmldoc)

    ##Get champion names
    name_divs = soup.find_all("div", {"class" : "champion-matchup-list__champion"})
    counters = re.findall(r"<span>(.*?)</span>", str(name_divs))
    win_rates = re.findall(r"([0123456789\.]{1,5})(?=%)", str(name_divs))

    win_rates, counters = zip(*sorted(zip(win_rates, counters)))


    # Display top five counters and their win rates

    message1 = "Best Counter: " + counters[0] + " | " + champion + " Win Rate: " + win_rates[0] + "%"
    message2 = "Second: " + counters[1] + " | " + champion + " Win Rate: " + win_rates[1] + "%"
    message3 = "Third: " + counters[2] + " | " + champion + " Win Rate: " + win_rates[2] + "%"
    message4 = "Fourth: " + counters[3] + " | " + champion + " Win Rate: " + win_rates[3] + "%"
    message5 = "Fifth: " + counters[4] + " | " + champion + " Win Rate: " + win_rates[4] + "%"

    await bot.say("The top five %s %s counters are: (op.gg)" % (champion,lane))
    await bot.say(message1)
    await bot.say(message2)
    await bot.say(message3)
    await bot.say(message4)
    await bot.say(message5)

def get_most_popular_lane(champion, message=False):
    #Hack to determine most popular lane (a request to op.gg for a champion's statistics redirects by default to their most popular lane)
    #Get redirected URL
    lane_test_request = urllib.request.urlopen('http://na.op.gg/champion/{}/statistics/'.format(champion))
    lane_test_url = lane_test_request.geturl()
    #Pull lane from URL
    exp = re.compile('\/[A-Za-z]*')
    matches = exp.findall(lane_test_url)
    lane = matches[-1][1:]
    #If desired, print a helpful message
    if message:
        await bot.say('No lane selected. Defaulting to {}\'s most popular lane, {}. ' \
            'If you want another lane, try something like this: "?items {} {}"'.format(champion, lane, champion, lane))
    return lane

bot.run("Mzk0MjcxMjIxNjc3Njg2Nzk0.DSxz6A.Rj5IaLDsiEPwMQ2nX1GW6XL7_ZY")
