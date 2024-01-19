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
play_task = None
queue = []

class music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='play')
    async def play(self, ctx, *, search_query):
        global paused_at, filename, inactive_task, video_id, queue, play_task
        
        #checks if bot already connected
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if voice_client is not None and voice_client.is_playing():
            # If it is, add the new song to the queue
            queue.append(search_query)
            await ctx.send('adicionado a fila')
            return

        #checks if there is any paused audio
        if voice_client is not None and voice_client.is_paused():
            if ((datetime.now() - paused_at).total_seconds() < 600):
                queue.append(search_query)
                if queue:
                    await ctx.send('adicionado a fila, use "!continue" ou "!next"')
                return
            if ((datetime.now() - paused_at).total_seconds() > 600):
                voice_client.stop()
                await asyncio.sleep(0.5)
                if filename:
                    try:
                        os.remove(filename)
                    except FileNotFoundError:
                        pass
                    except PermissionError as e:
                            await ctx.send(f'error: unable to delete file>    {e}  ')
                            
                filename = None
                paused_at = datetime.now()
        
        if play_task is None or play_task.done():
            play_task = asyncio.create_task(self.play(ctx, search_query))
        
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

            else:
                # Construct the full YouTube URL
                video_url = f'https://www.youtube.com/watch?v={first}'
        
        # Use pytube to download the audio    
        yt = pytube.YouTube(video_url)
        
        
        max_bitrate = 128 # Maximum allowed bitrate in kbps
        selected_stream = None
        for stream in yt.streams.filter(only_audio=True):
            abr = int(stream.abr) if stream.abr.isdigit() else 0
        if abr <= max_bitrate and (selected_stream is None or abr > int(selected_stream.abr)):
            selected_stream = stream
        stream = selected_stream
        # stream = max(yt.streams.filter(only_audio=True), key=lambda s: s.abr)
        out_file = stream.download(filename='temp')
        filename = os.path.join('temp', out_file)
        
        #play the audio    
        voice_client.play(discord.FFmpegPCMAudio(executable='ffmpeg', source=filename))
        await ctx.send(f'tocando: {video_url}')
        
        # Wait until the audio is finished playing and delete the file    
        while voice_client.is_playing():
            await asyncio.sleep(1)
        if not voice_client.is_paused():
            if filename is not None:
                try:
                    os.remove(filename)
                except FileNotFoundError:
                    pass
        
        # If there are songs in the queue, play the next song   
        if queue:
            next_song = queue.pop(0)
            voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            if not voice_client.is_paused():
                await ctx.invoke(self.bot.get_command('play'), search_query=next_song)
                
        #checks if the there is an instance of inactivity
        if inactive_task is not None:
            inactive_task.cancel()
                
        inactive_task = self.bot.loop.create_task(disconnect_if_inactive(voice_client))



    @commands.command(name='pause') #done
    async def pause(self, ctx):
        global paused_at, filename
        
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if voice_client.is_playing():
            voice_client.pause()
            paused_at = datetime.now()
            await ctx.send('audio pausado')
            return
        else:
            await ctx.send('nenhum audio tocando no momento')
            return

        
    @commands.command(name='continue') #done
    async def Continue(self, ctx):
        global paused_at, filename, play_task, should_stop
        
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if (voice_client.is_paused() and (datetime.now() - paused_at).total_seconds() < 600):
                voice_client.resume()
                paused_at = datetime.now()
                should_stop = True
                await ctx.send('resumindo audio')
                return
                
        if (paused_at is not None and (datetime.now() - paused_at).total_seconds() > 600):
            voice_client.stop()
            await asyncio.sleep(0.5)
            if filename is not None:
                try:
                    os.remove(filename)
                    await ctx.send('nenhum audio pausado no momento') 
                    return
                except FileNotFoundError:
                    pass
                except PermissionError as e:
                    await ctx.send(f'error: unable to delete file>    {e}  ')
        
        if play_task is not None and not play_task.done():
            await ctx.send('audio já está tocando')

        else:
            await ctx.send('nenhum audio pausado no momento')

        
        
        
    @commands.command(name='next') #works
    async def next(self, ctx):
        global filename, queue, paused_at
        
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if (voice_client.is_playing() or voice_client.is_paused()) and len(queue) > 0:
            voice_client.stop()
            await asyncio.sleep(0.5)
            if filename is not None:
                try:
                    os.remove(filename)
                except FileNotFoundError:
                    pass
                except PermissionError as e:
                    await ctx.send(f'error: unable to delete file>   {e} ')
            filename = None
            paused_at = datetime.now()
            
        if queue:
            next_song = queue.pop(0)
            await ctx.invoke(self.bot.get_command('play'), search_query= next_song)
            return
        else:
            await ctx.send('nenhuma musica na fila')

            
            
            
    @commands.command(name='stop')
    async def stop(self, ctx):
        global filename, queue, paused_at, play_task
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if voice_client is not None and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()
            await asyncio.sleep(0.5)
            if filename is not None:
                try:
                    os.remove(filename)
                except FileNotFoundError as e:
                    await ctx.send(f'error: unable to delete file> {e}')
                    return
            filename = None
            queue.clear()
            await ctx.send('todos os videos na fila foram parados')
            
            # Cancel any pending tasks related to the play command
            if play_task is not None and not play_task.done():
                play_task.cancel()
            return
        else:
            await ctx.send('ta doido nengue, tem nada pra parar não')

            
async def setup():
    await bot.add_cog(music(bot))
    
@bot.event
async def on_ready():
    await setup()




















    # Run the bot with your token
bot.run('MTE5Njg5NzgzMzAzMTMwMzMzOA.GKQTh_.f_l0vYlLYEvfe-sErC4L-9IhYdjubxlipusuzY')