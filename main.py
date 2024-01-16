import discord
from discord.ext import commands
import urllib.request
import pytube
import os
import re
import asyncio
from configs import youtube_url_validation

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)



@bot.command(name='play')
async def play(ctx, *, search_query):
    if not ctx.author.voice:
        await ctx.send('tu não tá no voice chat nengue')
        return
    
    if not youtube_url_validation(search_query):   
        search_query = search_query.replace(' ', '+')
        html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={search_query}')
        video_id = re.findall(r'watch\?v=(\S{11})', html.read().decode())
        first = video_id[0] if video_id else None
        
        if not first:
            await ctx.send('achei teu video não nengue')
            return

        # Construct the full YouTube URL
        video_url = f'https://www.youtube.com/watch?v={first}'

        # Use pytube to download the audio
        yt = pytube.YouTube(video_url)
        stream = max(yt.streams.filter(only_audio=True), key=lambda s: s.abr)
        #stream = yt.streams.filter(only_audio=True).first()
        out_file = stream.download(filename='temp')
        filename = os.path.join('temp', out_file)

        # Connect to the voice channel and play the audio
        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=filename))

        # Wait until the audio is finished playing
        while voice_client.is_playing():
            await asyncio.sleep(1)

        # Disconnect from the voice channel and delete the temp file
        await voice_client.disconnect()
        os.remove(filename)

    # Run the bot with your token
bot.run('MTE5Njg5NzgzMzAzMTMwMzMzOA.GKQTh_.f_l0vYlLYEvfe-sErC4L-9IhYdjubxlipusuzY')