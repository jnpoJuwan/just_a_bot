import discord
from discord.ext import commands

from ._utils.constants import COLOUR


class Images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"INFO: {__name__} is ready.")

    @commands.command()
    async def icon(self, ctx):
        """Send the server's icon."""
        async with ctx.typing():
            embed = discord.Embed(title=f"{ctx.guild.name}'s icon", colour=COLOUR)
            embed.set_image(url=ctx.guild.icon_url)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["avatar", "profile_picture"])
    async def pfp(self, ctx, member: discord.Member = None):
        """Send the profile picture of a member. Send the author's profile picture if no member is specified."""
        if member is None:
            member = ctx.author

        async with ctx.typing():
            embed = discord.Embed(title=f"{member}'s avatar", colour=COLOUR)
            embed.set_image(url=member.avatar_url)
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    # Exception Handling.

    @pfp.error
    async def member_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please @mention a member.")


def setup(bot):
    bot.add_cog(Images(bot))
