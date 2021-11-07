#!/usr/bin/env python3.8

import os
import discord
from discord import user
from discord.ext import commands
from discord.ext.commands import dm_only
from dotenv import load_dotenv
import json
from supabase import create_client, Client

ENV_FILE = ".env"
load_dotenv(ENV_FILE)

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

GAME_FILE = "game.json"
with open(GAME_FILE) as f:
    game = json.load(f)

FLAG=["shellmates","where_there_is_a_shell,","there_is_a_way_2121"]

HELP_MSG = '''\
```
help     Shows this message
  Usage:    $help
play     Use it to start playing
  Usage:    $play
flag     Use it to submit a part of the flag
  Usage:    $flag <flag_part>
  Example:  $flag shellmates
status   Show your progression in the challenge
  Usage:    $status
```\
'''


bot = commands.Bot(command_prefix="$")
bot.remove_command("help")

def embed(message):
  embedVar=discord.Embed(title=message['title'], description=message['description'], color=0x00ff00)
  if(len(message['hint'])>0):
    embedVar.add_field(name="Hint", value=message['hint'], inline=False)
  return embedVar if message else ""




@bot.event
async def on_ready():
    print(f"{bot.user.name} connection to Discord established.")
    for guild in bot.guilds:
        print(f"[+] {bot.user} connected to {guild}")
    await bot.change_presence(activity=discord.Game(name="$help"))
    os.unsetenv("SUPABASE_URL")
    os.unsetenv("SUPABASE_KEY")
    os.unsetenv("DISCORD_TOKEN")
    os.remove(ENV_FILE)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('```Missing one or more positional arguments.\n$help <command> for more information.```')
        return

    if isinstance(error, commands.CommandNotFound):
        await ctx.send('```Command does not exist.\n$help for more information about the available commands.```')
        return

    if isinstance(error, commands.PrivateMessageOnly):
        await ctx.send('```:lock: DMs only\nThis bot is only available in direct messages```')
        return

@bot.command(name="help", help="Show this message")
async def help(ctx):
    dm_channel = await ctx.author.create_dm()
    await dm_channel.send(HELP_MSG)

@bot.command(name="play", help="Start playing")
@dm_only()
async def play(ctx):
  user =supabase.table("player").select("*").eq("name",f"{ctx.message.author}").execute() 
  if not len(user.get("data", [])) > 0:
    user=supabase.table("player").insert({"name":f"{ctx.message.author}"}).execute()
  user=supabase.table("player").select("*").eq("name",f"{ctx.message.author}").execute()
  user=user.get("data")[0]["solved"]

  await ctx.send(embed=embed(game[f"{user}"]))

@bot.command(name="flag", help="submit a flag part")
@dm_only()
async def flag(ctx, string):
  user =supabase.table("player").select("*").eq("name",f"{ctx.message.author}").execute() 
  if not len(user.get("data", [])) > 0:
    user=supabase.table("player").insert({"name":f"{ctx.message.author}"}).execute()
  user=supabase.table("player").select("*").eq("name",f"{ctx.message.author}").execute()
  solved=user.get("data")[0]["solved"]
  if solved==3:
    await ctx.send(f'```\nYou are already a winner !\n```')
    return  
  else: 
    for i in range(3):
      if FLAG[i]==string:
        if solved==i:
          supabase.table("player").update({"solved":(i+1)}).eq("name",f"{ctx.message.author}").execute()
          user=supabase.table("player").select("*").eq("name",f"{ctx.message.author}").execute()
          solved=user.get("data")[0]["solved"]
          if solved==3:
            supabase.table("winners").insert({"name":f"{ctx.message.author}"}).execute()
          await play(ctx)
          return
        elif solved>i:
          await ctx.send(f'```\nYou have already submitted this part, Go find the other parts!\n```')
          return
        else:
          await ctx.send(f'```\nThis is the part nb : "{i+1}", you must submit the first parts before.\n```')
          return
    await ctx.send('```\nNo gift for you !!!\n```')
    return

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
