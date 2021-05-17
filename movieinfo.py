import requests, re, json, os, urllib.request, shutil, random, traceback

from io import BytesIO

from telethon import TelegramClient, events

from country_list import countries_for_language

token = os.getenv("TOKEN")
app_id = int(os.getenv("APP_ID"))
app_hash = os.getenv("APP_HASH")
tmdb_key = 'b729fb42b650d53389fb933b99f4b072'
header = {'User-Agent': 'Kodi Movie scraper by Team Kodi'}

tmdb_id = []
for item in open('movieid'):
    tmdb_id.append(item.strip("\n"))

langcode = {}
for line in open('langcode'):
    key, value = line.split(' ')
    langcode[key] = value.strip('\n')

status_dic = {
        'Returning Series': '在播',
        'Ended': '完结',
        'Canceled': '被砍',
        'In Production': '拍摄中'
        }

def get_translation(text):
    result = requests.get('https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-cn&&dt=t&q='+requests.utils.quote(text)).json()[0][0][0]
    return result

bot = TelegramClient('bot', app_id, app_hash).start(bot_token=token)

@bot.on(events.NewMessage(pattern=r'^/m\s'))
async def movie_info(event):
    chat_id = event.message.chat_id
    msg = re.sub(r'/m\s*', '', event.message.text)
    if re.search(r'\s\d*$', msg):
        search_query = re.match(r'.*\s', msg).group()[:-1]+'&year='+re.search(r'\s\d*$', msg).group()
    else:
        search_query = msg
    search_url = 'https://api.themoviedb.org/3/search/movie?api_key='+tmdb_key+'&language=zh-CN&query='+search_query
    try:
        tmdb_id = requests.get(search_url).json()['results'][0]['id']
    except:
        await bot.send_message(chat_id, '好像没搜到，换个名字试试')
        return None
    try:
        tmdb_info = requests.get('https://api.themoviedb.org/3/movie/'+str(tmdb_id)+'?api_key='+tmdb_key+'&language=zh-CN').json()
        trailer_list = requests.get('https://api.themoviedb.org/3/movie/'+str(tmdb_id)+'/videos?api_key='+tmdb_key).json()['results']
        trailer_url = None
        for i in trailer_list:
            if i['site'] == 'YouTube':
                if i['type'] == 'Trailer':
                    trailer_url = 'https://www.youtube.com/watch?v='+i['key']
                    break
        if trailer_url is None:
            trailer = ''
        else:
            trailer = ' [预告片]('+trailer_url+')'
        imdb_id = requests.get('https://api.themoviedb.org/3/movie/'+str(tmdb_id)+'/external_ids?api_key='+tmdb_key).json()['imdb_id']
        imdb_rating = re.search(r'"ratingValue">\d\.\d', requests.get('https://www.imdb.com/title/'+imdb_id+'/').text).group()[-3:]
        poster = BytesIO(requests.get('https://www.themoviedb.org/t/p/w600_and_h900_bestv2'+tmdb_info['poster_path'], headers=header).content)
        countries = dict(countries_for_language('zh_CN'))
        tmdb_credits = requests.get('https://api.themoviedb.org/3/movie/'+str(tmdb_id)+'/credits?api_key='+tmdb_key).json()
        for crew in tmdb_credits['crew']:
                if crew['job'] == 'Director':
                    director = re.sub('（.*）', '', get_translation(crew['name']))
                    break
        language = langcode[tmdb_info['original_language']]
        actors = re.sub('（.*）', '', get_translation(tmdb_credits['cast'][0]['name']))+'\n'
        for item in tmdb_credits['cast'][1:5]:
            actor = re.sub('（.*）', '', get_translation(item['name']))
            actors = actors+'         '+actor+'\n'
        genres = ''
        for genre in tmdb_info['genres'][:2]:
            genres = genres+' #'+genre['name']
            info = '**'+tmdb_info['title']+' '+tmdb_info['original_title']+' ('+tmdb_info['release_date'][:4]+')**'+trailer+'\n\n'+tmdb_info['overview']+'\n\n导演 '+director+'\n类型'+genres+'\n国家 '+countries[tmdb_info['production_countries'][0]['iso_3166_1']]+'\n语言 '+language+'\n上映 '+tmdb_info['release_date']+'\n片长 '+str(tmdb_info['runtime'])+'分钟\n演员 '+actors+'\n#IMDB_'+imdb_rating[0]+' '+imdb_rating
        await bot.send_file(chat_id, poster, caption=info)
    except Exception as e:
        traceback.print_exc()
        await bot.send_message(chat_id, '此片信息不完整，详见：[链接](https://www.themoviedb.org/movie/'+str(tmdb_id)+')')

@bot.on(events.NewMessage(pattern=r'^/t\s'))
async def tv_info(event):
    chat_id = event.message.chat_id
    msg = re.sub(r'/t\s*', '', event.message.text)
    if re.search(r'\s\d*$', msg):
        search_query = re.match(r'.*\s', msg).group()[:-1]+'&first_air_date_year='+re.search(r'\s\d*$', msg).group()
    else:
        search_query = msg
    search_url = 'https://api.themoviedb.org/3/search/tv?api_key='+tmdb_key+'&language=zh-CN&query='+search_query
    try:
        tmdb_id = requests.get(search_url).json()['results'][0]['id']
    except:
        await bot.send_message(chat_id, '好像没搜到，换个名字试试')
        return None
    try:
        tmdb_info = requests.get('https://api.themoviedb.org/3/tv/'+str(tmdb_id)+'?api_key='+tmdb_key+'&language=zh-CN').json()
        trailer_list = requests.get('https://api.themoviedb.org/3/tv/'+str(tmdb_id)+'/videos?api_key='+tmdb_key).json()['results']
        trailer_url = None
        for i in trailer_list:
            if i['site'] == 'YouTube':
                if i['type'] == 'Trailer':
                    trailer_url = 'https://www.youtube.com/watch?v='+i['key']
                    break
        if trailer_url is None:
            trailer = ''
        else:
            trailer = ' [预告片]('+trailer_url+')'
        imdb_id = requests.get('https://api.themoviedb.org/3/tv/'+str(tmdb_id)+'/external_ids?api_key='+tmdb_key).json()['imdb_id']
        trakt_rating = str(requests.get('https://api.trakt.tv/shows/'+imdb_id+'/ratings', headers={'trakt-api-key': '4fb92befa9b5cf6c00c1d3fecbd96f8992c388b4539f5ed34431372bbee1eca8'}).json()['rating'])[:3]
        poster = BytesIO(requests.get('https://www.themoviedb.org/t/p/w600_and_h900_bestv2'+tmdb_info['poster_path'], headers=header).content)
        countries = dict(countries_for_language('zh_CN'))
        tmdb_credits = requests.get('https://api.themoviedb.org/3/tv/'+str(tmdb_id)+'/credits?api_key='+tmdb_key).json()
        creator = ''
        for person in tmdb_info['created_by']:
                    creator = creator+' '+re.sub('（.*）', '', get_translation(person['name']))
        actors = re.sub('（.*）', '', get_translation(tmdb_credits['cast'][0]['name']))+'\n'
        for item in tmdb_credits['cast'][1:5]:
            actor = re.sub('（.*）', '', get_translation(item['name']))
            actors = actors+'         '+actor+'\n'
        genres = ''
        for genre in tmdb_info['genres'][:2]:
            genres = genres+' #'+genre['name']
        seasons = ''
        for season in tmdb_info['seasons']:
            seasons = seasons+season['name']+' - 共'+str(season['episode_count'])+'集\n'
        status = status_dic[tmdb_info['status']]
        info = '**'+tmdb_info['name']+' '+tmdb_info['original_name']+' ('+tmdb_info['first_air_date'][:4]+')**'+trailer+'\n\n'+tmdb_info['overview']+'\n\n创作'+creator+'\n类型'+genres+'\n国家 '+countries[tmdb_info['origin_country'][0]]+'\n网络 #'+tmdb_info['networks'][0]['name']+'\n状况 '+status+'\n首播 '+tmdb_info['first_air_date']+'\n集长 '+str(tmdb_info['episode_run_time'][0])+'分钟\n演员 '+actors+'\n分季概况：\n'+seasons+'\n#Trakt_'+trakt_rating[0]+' '+trakt_rating
        await bot.send_file(chat_id, poster, caption=info)
    except Exception as e:
        traceback.print_exc()
        await bot.send_message(chat_id, '此剧信息不完整，详见：[链接](https://www.themoviedb.org/tv/'+str(tmdb_id)+')')

@bot.on(events.NewMessage(pattern=r'^出题$|^出題$'))
async def send_question(event):
    sender = event.message.sender
    id = str(random.choice(tmdb_id))
    tmdb_info = requests.get('https://api.themoviedb.org/3/movie/'+id+'?api_key='+tmdb_key+'&language=zh-CN').json()
    image_list = requests.get('https://api.themoviedb.org/3/movie/'+id+'/images?api_key='+tmdb_key).json()['backdrops']
    try:
        sender_name = sender.first_name
    except:
        sender_name = 'BOSS'
    caption1 = sender_name+' 问，这部'+tmdb_info['release_date'][:4]+'年的'+tmdb_info['genres'][0]['name']+'影片的标题是？(60秒内作答有效)'
    print(tmdb_info['title'])
    title_list = []
    title_info = requests.get('https://api.themoviedb.org/3/movie/'+id+'/alternative_titles?api_key='+tmdb_key+'&country=CN').json()['titles']
    info_url = 'https://www.themoviedb.org/movie/'+str(tmdb_info['id'])   
    for t in title_info:
        title_list.append(t['title'])
    translation_info = requests.get('https://api.themoviedb.org/3/movie/'+id+'/translations?api_key='+tmdb_key+'&country=CN').json()['translations']
    for t in translation_info:
        title_list.append(t['data']['title'])
    try:
        image_url = 'https://www.themoviedb.org/t/p/original'+random.choice(image_list)['file_path']
    except:
        image_url = 'https://www.themoviedb.org/t/p/original'+tmdb_info['poster_path']
    image = BytesIO(requests.get(image_url, headers=header).content)
    try:
        async with bot.conversation(event.message.chat_id, exclusive=False, total_timeout=60) as conv:
            question = await conv.send_file(image, caption=caption1)
            while True:
                response = await conv.get_response()
                try:
                    responder_name = response.sender.first_name
                except:
                    responder_name = 'BOSS'
                answer = response.text
                for a in title_list:
                    if a != '':
                        if re.match(re.escape(a[:5]), answer, re.IGNORECASE):
                            caption2 = responder_name+' 回答正确！\n**'+tmdb_info['title']+' '+tmdb_info['original_title']+' ('+tmdb_info['release_date'][:4]+')** '+'[链接]('+info_url+')'
                            await bot.send_message(event.message.chat_id, caption2, reply_to=response)
                            return
    except Exception as e:
        print(e)
        await bot.edit_message(question, '答题超时，答案：'+tmdb_info['title'])

if __name__ == '__main__':
    bot.start()
    bot.run_until_disconnected()
