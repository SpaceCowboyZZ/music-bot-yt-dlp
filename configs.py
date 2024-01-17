import re
import pytube
import discord
from discord.ext import commands
import os
import asyncio


#regex to validate youtube link
def youtube_url_validation(url):
   youtube_regex = (
       r'(https?://)?(www\.)?'
       '(youtube|youtu|youtube-nocookie)\.(com|be)/'
       '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
   
   youtube_match = re.match(youtube_regex, url)
   if youtube_match:
       return True
   else:
       return False
   
async def disconnect_if_inactive(voice_client, timeout=900):
    await asyncio.sleep(timeout)
    if not voice_client.is_playing() and not voice_client.is_paused():
        await voice_client.disconnect()