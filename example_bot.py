# coding=UTF-8

import discord
from discord.ext.commands import Bot
from discord.ext import commands
from avalon import Avalon

bot = Bot(command_prefix="!")
bot.add_cog(Avalon(bot))
bot.run("----------bot-token----------")