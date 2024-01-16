import re

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