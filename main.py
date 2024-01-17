import discord
from discord.ext import commands
import urllib.request
import pytube
import os
import re
import asyncio
from configs import youtube_url_validation, disconnect_if_inactive

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

inactive_task = None

@bot.command(name='play')
async def play(ctx, *, search_query):
    #checks if bot already connected
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    #conects to voice if not connected already, also sends message if you are not in a voice chat
    if not voice_client:
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            voice_client = await voice_channel.connect()
        else:
            await ctx.send('tu não ta no voice chat nengue.')
            return
        
     #replace empty spaces with '+' so the link will work
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
    stream = max(yt.streams.filter(only_audio=True), key=lambda s: s.abr)#finds the highest bitrate audio
    out_file = stream.download(filename='temp')
    filename = os.path.join('temp', out_file)

        # Connect to the voice channel and play the audio
    voice_channel = ctx.author.voice.channel
    voice_client = await voice_channel.connect()
    voice_client.play(discord.FFmpegPCMAudio(executable="ffmpeg", source=filename))

        # Wait until the audio is finished playing and delete the file
    while voice_client.is_playing():
        await asyncio.sleep(1)
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
        
    if youtube_url_validation(search_query):
        video_url = search_query
        yt = pytube.YouTube(video_url)
        stream = max(yt.streams.filter(only_audio=True), key=lambda s: s.abr)
        out_file = stream.download(filename='temp')
        filename = os.path.join('temp', out_file)
        
        voice_channel = ctx.author.voice.channel
        voice_client = await voice_channel.connect()
        voice_client.play(discord.FFmpegPCMAudio(executable='ffmpeg', source=filename))
        
        while voice_client.is_playing():
            await asyncio.sleep(1)
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass
            
        #checks if the there is an instance of inactivity
        if inactive_task is not None:
            inactive_task.cancel()
            
        inactive_task = bot.loop.create_task(disconnect_if_inactive(voice_client))


@bot.command(name='stop')
async def stop(ctx):
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_playing():
        voice_client.stop()
        
    await ctx.send('num tem nada tocando não Cleide')






















    # Run the bot with your token
bot.run('MTE5Njg5NzgzMzAzMTMwMzMzOA.GKQTh_.f_l0vYlLYEvfe-sErC4L-9IhYdjubxlipusuzY')