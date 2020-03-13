import asyncio
import discord
from discord.ext import commands

class Dialog:
    def __init__(self, *initial_data, **kwargs):
        self.title = ""
        self.content = ""
        self.color = 0x73a936
        self.name =""
        self.icon_url = ""
        self.footer_text = ""
        self.image_url = ""
        self.thumbnail_url = ""
        self.timeout = 300.0
        self.embed = None
        self.buttons = []
        self.check = lambda reaction, user: user.id != self.bot.user.id and str(reaction.emoji) in self.buttons and (self.valid == user.id or type(self.valid) == list and user.id in self.valid or type(self.valid) == dict and (str(reaction.emoji) in self.valid.keys() and user.id in self.valid[str(reaction.emoji)] or str(reaction.emoji) not in self.valid.keys()))
        self.message = None
        self.bot = None
        self.valid = {}

        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])
        
        self.update_embed()

    def __call__(self):
        return self.update_embed()

    def update_embed(self):
        self.embed = discord.Embed(title=self.title, description=self.content, color=self.color)
        self.embed.set_author(name=self.name,icon_url=self.icon_url)
        if self.footer_text != "":
            self.embed.set_footer(text=self.footer_text)
        if self.image_url != "":
            self.embed.set_image(url=self.image_url)
        if self.thumbnail_url != "":
            self.embed.set_thumbnail(url=self.thumbnail_url)

        return self.embed
    
    async def send_dialog_message(self, target):
        if self.embed is None:
            self.update_embed()
        self.message = await target.send(embed=self.embed)
        if len(self.buttons) > 0:
            await self.send_buttons()
        return self.message

    async def edit(self):
        return await self.message.edit(embed=self.embed)

    async def send_buttons(self):
        # tasks = []
        for button in self.buttons:
            # tasks.append(self.message.add_reaction(button))
            await self.message.add_reaction(button)
        
        # return await asyncio.wait(tasks)

    async def add_button(self, button):
        self.buttons.append(button)
        return await self.message.add_reaction(button)
    
    async def remove_button(self, button):
        return await self.message.clear_reaction(button)
    
    async def wait_respond(self):
        return await self.bot.wait_for(event='reaction_add', timeout=self.timeout, check=self.check)
    
    async def reset_button(self, button, user):
        return await self.message.remove_reaction(button, user)
    
    async def close(self):
        return await self.message.delete()
