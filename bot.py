from discord.ext import commands
import discord
import html
from pymongo import MongoClient
import pymongo
from bson import json_util
import json

with open("config.json") as conf:
    config = json.load(conf)
    token = config["token"]
    prefix = config["prefix"]
    database = config["database"]
    description = config["description"]

client = MongoClient(database)
db = client["discordsites"]
doc = db["guilds"]

class Core:
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.is_owner()
    async def searchguilds(self, ctx, guild_id: int):
        """Search for guild in database"""
        info = doc.find_one({"guild_id": guild_id})
        info = json.dumps(info, indent=4, sort_keys=True, default=json_util.default)
        await ctx.send(f"```json\n{info}```")
    
    @commands.command()
    @commands.is_owner()
    async def guildscount(self, ctx):
        """Guilds count"""
        count = doc.count({})
        await ctx.send(f"Found `{count}` documents in the `guilds` collection (of the `DiscordSites` database).")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def updatestats(self, ctx):
        """Update guild page stats"""
        guild = ctx.guild
        await self.update_guild(guild)
        await ctx.send("Done")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def togglepage(self, ctx):
        """Toggle the guild page"""
        guild = ctx.guild
        await self.update_guild(guild)
        info = doc.find_one({"guild_id": guild.id})
        if info["toggle"] == 0:
            doc.update_one({"guild_id": guild.id}, {"$set": {"toggle": 1}} )
            await ctx.send("Activated")
        else:
            doc.update_one({"guild_id": guild.id}, {"$set": {"toggle": 0}} )
            await ctx.send("Deactivated")
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setdescription(self, ctx, *, description):
        """Set guild page description"""
        guild = ctx.guild
        await self.update_guild(guild)
        description = await self.clean_description(description)
        doc.update_one({"guild_id": guild.id}, {"$set": {"guild_description": description}} )
        await ctx.send("Done")

    async def on_guild_join(self, guild):
        await self.update_guild(guild)

    async def on_member_join(self, member):
        guild = member.guild
        await self.update_guild(guild)

    async def update_guild(self, guild):
        if doc.find_one({"guild_id": guild.id}) is None:
            data = {"guild_id": guild.id, "guild_name": guild.name, "guild_icon": guild.icon_url_as(format="png", size=256), "guild_membercount": len(guild.members), "guild_description": "", "guild_background": "https://check-out.isabel.moe/eNzQjVT.png", "toggle": 0}
            doc.insert_one(data)
            invite = await self.get_invite(guild)
            doc.update_one({"guild_id": guild.id}, {"$set": {"guild_invite": invite}} )
            return
        doc.update_one({"guild_id": guild.id}, {"$set": {"guild_name": guild.name, "guild_icon": guild.icon_url_as(format="png", size=256), "guild_membercount": len(guild.members)}} )

    async def clean_description(self, description):
        description = html.escape(description)
        return description

    async def get_invite(self, guild):
        for chan in guild.text_channels:
            try:
                inv = await chan.create_invite()
                return inv.url
            except:
                pass
        return "#"

bot = commands.AutoShardedBot(command_prefix=commands.when_mentioned_or(prefix), description=description)

@bot.event
async def on_ready():
    print("Logged in as {0.id}/{0}".format(bot.user))
    print("--------------------------------------------------")

bot.add_cog(Core(bot))
bot.run(token)
