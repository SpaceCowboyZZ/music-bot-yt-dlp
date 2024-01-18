import discord
import time
from datetime import datetime
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
filename = None
paused_at = None
queue = []




@bot.command(name='play')
async def play(ctx, *, search_query):
    global paused_at, filename, inactive_task, video_id, queue
    #checks if bot already connected
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client is not None and voice_client.is_playing():
        # If it is, add the new song to the queue
        queue.append(search_query)
        await ctx.send('adicionado a fila')
        return
    
    #checks if there is any paused audio
    if voice_client is not None and voice_client.is_paused():
        if (datetime.now() - paused_at).total_seconds() < 6:
            queue.append(search_query)
            await ctx.send('adicionado a fila, use "!continue" ou "!next"')
            return
        
        else:
            if (datetime.now() - paused_at).total_seconds() > 6:
                voice_client.stop()
                await asyncio.sleep(0.5)
                if filename:
                    try:
                        os.remove(filename)
                    except FileNotFoundError:
                        pass
                    except PermissionError as e:
                        await ctx.send(f'error: unable to delete file>    {e}  ')
                        return
            filename = None
            paused_at = datetime.now()
    
    #conects to voice if not connected already, also sends message if you are not in a voice chat
    if not voice_client:
        if ctx.author.voice:
            voice_channel = ctx.author.voice.channel
            voice_client = await voice_channel.connect()
        else:
            await ctx.send('tu não ta no voice chat nengue.')
            return

    if youtube_url_validation(search_query):
        video_url = search_query
    else:
        #replace empty spaces with '+' so the link will work
        search_query = search_query.replace(' ', '+')
        html = urllib.request.urlopen(f'https://www.youtube.com/results?search_query={search_query}')
        video_id = re.findall(r'watch\?v=(\S{11})', html.read().decode())
        first = video_id[0] if video_id else None
        if not first:
            await ctx.send('não encrontrado')
            return
        else:
            # Construct the full YouTube URL
            video_url = f'https://www.youtube.com/watch?v={first}'
    
    # Use pytube to download the audio    
    yt = pytube.YouTube(video_url)
    stream = max(yt.streams.filter(only_audio=True), key=lambda s: s.abr)
    out_file = stream.download(filename='temp')
    filename = os.path.join('temp', out_file)
    
    #play the audio    
    voice_client.play(discord.FFmpegPCMAudio(executable='ffmpeg', source=filename))
    await ctx.send(f'tocando: {video_url}')
    
    # Wait until the audio is finished playing and delete the file    
    while voice_client.is_playing():
        await asyncio.sleep(1)
    if not voice_client.is_paused():
        try:
            os.remove(filename)
        except FileNotFoundError:
            pass
     
    # If there are songs in the queue, play the next song   
    if queue:
        next_song = queue.pop(0)
        await ctx.invoke(bot.get_command('play'), search_query=next_song)
            
    #checks if the there is an instance of inactivity
    if inactive_task is not None:
        inactive_task.cancel()
            
    inactive_task = bot.loop.create_task(disconnect_if_inactive(voice_client))



@bot.command(name='pause') #done
async def pause(ctx):
    global paused_at, filename
    
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client.is_playing():
        voice_client.pause()
        paused_at = datetime.now()
        await ctx.send('audio pausado')
    else:
        await ctx.send('nenhum audio tocando no momento')
    


@bot.command(name='continue') #done
async def Continue(ctx):
    global paused_at, filename
    
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if voice_client.is_paused():
        if (datetime.now() - paused_at).total_seconds() < 6:
            voice_client.resume()
            paused_at = datetime.now()
            await ctx.send('resumindo audio')      
            
        if paused_at is not None and (datetime.now() - paused_at).total_seconds() > 6:
            voice_client.stop()
            await asyncio.sleep(0.5)
            if filename:
                try:
                    os.remove(filename)
                    await ctx.send('nenhum audio pausado no momento')
                except FileNotFoundError:
                    pass
                except PermissionError as e:
                    await ctx.send(f'error: unable to delete file>    {e}  ')
    
    elif voice_client.is_playing():
        await ctx.send('audio já está tocando')
        
    else:
        await ctx.send('nenhum audio pausado no momento')
    
    
    
@bot.command(name='next')
async def next(ctx):
    global filename, queue
    
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    
    if (voice_client.is_playing() or voice_client.is_paused()) and len(queue) > 0:
        voice_client.stop()
        await asyncio.sleep(0.5)
        if filename:
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass
            except PermissionError as e:
                await ctx.send(f'error: unable to delete file>   {e} ')
        
        if queue:
            next_song = queue.pop(0)
            await ctx.invoke(bot.get_command('play'), search_query= next_song)
    else:
        await ctx.send('nenhuma musica na fila')
        
    























    # Run the bot with your token
bot.run('MTE5Njg5NzgzMzAzMTMwMzMzOA.GKQTh_.f_l0vYlLYEvfe-sErC4L-9IhYdjubxlipusuzY')