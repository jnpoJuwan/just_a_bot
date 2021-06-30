import random

import discord
import googletrans
import requests
from async_cse import Search
from bs4 import BeautifulSoup
from discord.ext import commands
from googletrans import Translator
from wiktionaryparser import WiktionaryParser
from youtube_search import YoutubeSearch

from ..configs.configs import GOOGLE_API_KEY
from ..utils import exceptions
from ..utils.constants import COLOUR, SPAM_LIMIT
from ..utils.paginator import ListPaginator

LANGUAGES = googletrans.LANGUAGES
LANG_CODES = googletrans.LANGCODES


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.google_client = Search(GOOGLE_API_KEY)
        self.parser = WiktionaryParser()
        self.translator = Translator()

    # XXX: This isn't the best implementation.
    # Its best use is creating a link to the Bolor website.
    @commands.command()
    async def bolor(self, ctx, *, query):
        """Searches Bolor Dictionary for a query."""
        page_list = []

        await ctx.trigger_typing()
        url = (f'http://www.bolor-toli.com/dictionary/word?search={query.replace(" ", "%20")}'
               f'&selected_lang=4-1&see_usages=false&see_variants=undefined')
        request = requests.get(url)
        soup = BeautifulSoup(request.text, 'lxml')

        if not soup.find('table', id='search_result_table'):
            await ctx.send('The word you\'ve entered isn\'t in Bolor Dictionary.')
            return

        raw_table = soup.find('table', id='search_result_table').find_all('tr')
        definitions = []

        # FIXME: Sometimes cuts off the first entry.
        for row in raw_table[1:]:
            try:
                source_cell, destination_cell = row.findChildren('td', width='50%')
            except ValueError:
                continue

            if source_cell.sup:
                source_cell.sup.replace_with(' ')
            if destination_cell.sup:
                destination_cell.sup.replace_with(' ')

            definitions.append((source_cell.text.strip(), destination_cell.text.strip()))

        chunk_list = ['']
        for source, destination in definitions:
            if len(chunk_list[-1]) > 1000:
                chunk_list.append('')
            chunk_list[-1] += f'\n• {source}: **{destination}**'

        i = 1

        for chunk in chunk_list:
            embed = discord.Embed(title='Bolor Dictionary', description=chunk, url=url, colour=COLOUR)
            embed.set_footer(text=f'Requested by {ctx.author.display_name} | Page {i}/{len(chunk_list)}',
                             icon_url=ctx.author.avatar_url)

            page_list.append(embed)
            i += 1

        paginator = ListPaginator(ctx, page_list)
        await paginator.start()

    @commands.command()
    async def choose(self, ctx, *args):
        """Chooses a random item from the list."""
        map(lambda x: x.strip(','), args)
        await ctx.send(f'**{random.choice(args)}**')

    @commands.command(aliases=['coin_flip', 'heads', 'tails'])
    async def flip_coin(self, ctx, amount=1):
        """Flips coins."""
        if amount >= SPAM_LIMIT:
            raise exceptions.SpamError

        output = ''.join([f'**{random.choice(["Heads", "Tails"])}**\n' for _ in range(amount)])
        await ctx.send(output)

    # CRED: @Tortoise-Community (https://github.com/Tortoise-Community/Tortoise-BOT/blob/master/bot/cogs/utility.py#L19)
    # NOTE: Google's Custom Search JSON API provides only 100 search queries per day for free.
    @commands.command(aliases=['g'])
    async def google(self, ctx, *, query):
        """Searches Google for a query."""
        page_list = []

        await ctx.trigger_typing()
        results = await self.google_client.search(query)
        i = 1

        for result in results:
            embed = discord.Embed(colour=COLOUR)
            embed.title = result.title
            embed.description = result.description
            embed.url = result.url

            embed.set_thumbnail(url=result.image_url)
            # TODO: Should be handled by paginator. <@Tortoise-Community>
            embed.set_footer(text=f'Requested by {ctx.author.display_name} | Page {i}/{len(results)} | {query}',
                             icon_url=ctx.author.avatar_url)

            page_list.append(embed)
            i += 1

        paginator = ListPaginator(ctx, page_list)
        await paginator.start()

    @commands.command(aliases=['vote'])
    async def poll(self, ctx, *, question):
        """Creates a basic yes/no poll."""
        embed = discord.Embed(title='Poll', description=question, colour=COLOUR)
        embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        await message.add_reaction('🤷')

    @commands.command(aliases=['poll_num'])
    async def pollnum(self, ctx, num=3, *, question):
        """Creates a basic poll with numbers."""
        if num > 10:
            await ctx.send('The amount of options can\'t exceed 10.')
            return

        num_list = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        embed = discord.Embed(title='Poll', description=question, colour=COLOUR)
        embed.set_footer(text=f'Requested by {ctx.author.display_name}', icon_url=ctx.author.avatar_url)
        message = await ctx.send(embed=embed)

        for i in range(num):
            await message.add_reaction(num_list[i])

    @staticmethod
    async def send_lang_codes(ctx):
        page_list = []

        await ctx.trigger_typing()
        code_list = sorted([f'{language.title()} – `{code}`\n' for language, code in LANG_CODES.items()])
        chunk_list = ['']
        i = 1

        for code in code_list:
            if chunk_list[-1].count('\n') >= 10:
                chunk_list.append('')
            chunk_list[-1] += code

        for chunk in chunk_list:
            embed = discord.Embed(title='Language Codes', description=chunk, colour=COLOUR)
            embed.set_footer(text=f'Requested by {ctx.author.display_name} | Page {i}/{len(chunk_list)}',
                             icon_url=ctx.author.avatar_url)

            page_list.append(embed)
            i += 1

        paginator = ListPaginator(ctx, page_list)
        await paginator.start()

    @commands.command(aliases=['gt', 'tr'])
    async def translate(self, ctx, source=None, destination=None, *, query=None):
        """Translate query into a language.

        The source and destination language arguments can be language codes or names.
        Surround language names with more than 1 word in quotes.
        Type `?translate` to fetch all valid language codes.
        """
        if not query:
            await self.send_lang_codes(ctx)
        else:
            source = source.lower()
            destination = destination.lower()

            # Change language names to language codes.
            if source in LANGUAGES.values():
                source = LANG_CODES[source]
            if destination in LANGUAGES.values():
                destination = LANG_CODES[destination]

            if source not in LANG_CODES.values() or destination not in LANG_CODES.values():
                await ctx.send('Invalid language(s).')
                return

            await ctx.trigger_typing()
            try:
                translation = self.translator.translate(query, dest=destination, src=source)
            except TypeError:
                await ctx.send('Something went wrong while translating.')
                return

            translated_text = translation.text

            if translation.pronunciation:
                if not isinstance(translation.pronunciation, str):
                    pass
                elif (translation.pronunciation == translation.origin
                      or translation.pronunciation == translation.text):
                    pass
                else:
                    translated_text += f'\n({translation.pronunciation})'

            embed = discord.Embed(colour=COLOUR)
            embed.title = f'Translate ({LANGUAGES[source].title()} > {LANGUAGES[destination].title()})'
            embed.description = translated_text

            embed.set_footer(text=f'Requested by {ctx.author.display_name} | Powered by Google Translate',
                             icon_url=ctx.author.avatar_url)

            await ctx.send(embed=embed)

    @commands.command(aliases=['dice', 'randint'])
    async def roll(self, ctx, faces: int = 20, amount: int = 1):
        """Rolls the number-sided dice."""
        if faces < 1:
            await ctx.send('Please enter a non-negative whole number.')
            return
        if amount >= SPAM_LIMIT:
            raise exceptions.SpamError

        for _ in range(amount):
            await ctx.send(f'**{random.randint(1, faces)}**')

    @roll.error
    async def roll_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send('Please enter a non-negative whole number.')

    @commands.command(aliases=['dict', 'dictionary', 'wikt'])
    async def wiktionary(self, ctx, language, *, query):
        """Search Wiktionary for a query.

        The language argument can be a language code or name.
        Surround language names with more than 1 word in quotes.
        """
        language = language.lower()
        page_list = []

        # Change language codes to language names.
        # NOFIX: LANGUAGES and LANG_CODES are only the languages recognised by Google Translate,
        # since there are 8 163 recognised language codes by Wiktionary.
        if language in LANG_CODES.values():
            language = LANGUAGES[language]

        await ctx.trigger_typing()
        results = self.parser.fetch(query, language)
        page_number = 0
        i = 1

        if not results:
            await ctx.send('Sorry. I couldn\'t find that word or language.')
            return

        # XXX: Looping around a list twice.
        for result in results:
            if not result['definitions']:
                await ctx.send('Sorry. I couldn\'t find that word or language.')
                return

            page_number += len(result['definitions'])

        for result in results:
            url = f'https://en.wiktionary.org/wiki/{query.replace(" ", "_")}#{language.title().replace(" ", "_")}'
            pronunciation = '\n'.join(['• ' + x for x in result['pronunciations']['text']]) or None
            etymology = result['etymology'] or None

            for definition in result['definitions']:
                headword = definition['text'][0]
                filler = '\xa0\xa0\xa0\xa0'
                definitions = ''.join([f'{filler}{j + 1}. {line}\n' for j, line in enumerate(definition['text'][1:])])
                content = headword + '\n' + definitions

                part_of_speech = definition['partOfSpeech'].title() or 'Definitions'

                embed = discord.Embed(title=query, url=url, colour=COLOUR)

                if pronunciation:
                    embed.add_field(name='Pronunciation', value=pronunciation, inline=False)
                if etymology:
                    embed.add_field(name='Etymology', value=etymology[:500], inline=False)

                embed.add_field(name=part_of_speech, value=content[:1000], inline=False)

                embed.set_footer(text=f'Requested by {ctx.author.display_name} | '
                                      f'Page {i}/{page_number} | Powered by Wiktionary',
                                 icon_url=ctx.author.avatar_url)

                page_list.append(embed)
                i += 1

        paginator = ListPaginator(ctx, page_list)
        await paginator.start()

    @commands.command(aliases=['yt'])
    async def youtube(self, ctx, *, query):
        """Search YouTube for a query."""
        page_list = []

        await ctx.trigger_typing()
        results = YoutubeSearch(query, max_results=20).to_dict()
        i = 1

        for result in results:
            embed = discord.Embed(title=result['title'], url=f'https://youtu.be/{result["id"]}', colour=COLOUR)

            if result['long_desc']:
                embed.description = result['long_desc']

            embed.set_thumbnail(url=result['thumbnails'][0])
            embed.set_footer(text=f'Requested by {ctx.author.display_name} | Page {i}/{len(results)} | {query}',
                             icon_url=ctx.author.avatar_url)

            page_list.append(embed)
            i += 1

        paginator = ListPaginator(ctx, page_list)
        await paginator.start()


def setup(bot):
    bot.add_cog(Utility(bot))
