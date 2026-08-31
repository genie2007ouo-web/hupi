import discord
from discord.ext import commands
from discord.ext import tasks
from datetime import time, timedelta, timezone,datetime
import yt_dlp
import asyncio
import random
import sys
import os
import json

# 設定權限
# 這是你程式碼的最上方
intents = discord.Intents.default()
intents.members = True          # 這一行絕對不能少！
intents.message_content = True  # 讓機器人能讀取指令
bot = commands.Bot(command_prefix='!', intents=intents)
TOKEN = os.getenv("DISCORD_TOKEN")

def parse_duration(duration):
    if duration is None: return "未知"
    
    duration = int(float(duration))
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def load_tarot():
    file_path = r"C:\Users\genie\dcbot\TAROT_RESPONSES.json"
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data
# 全域變數：儲存每個伺服器的播放清單
# 格式: {guild_id: [song_info1, song_info2, ...]}
queues = {}

# ==========================================
#                  配置區
# ==========================================
MORNING_RESPONSES = [
    "早安啊 {name}！今天也要元氣滿滿喔！☀️",
    "早安～你有沒有記得喝杯水呀？(,,・ω・,,)",
    "嗚哇...早安...我還想再睡五分鐘...（戳）",
    "早安！看到 {name} 出現我就開心了 (ﾉ>ω<)ﾉ",
    "早安！今天的早餐打算吃什麼呢？🥪",
    "（揉眼睛）早安早安！今天也是開心的一天٩(｡・ω・｡)و",
    "早安吶~~今天有記得吃藥嗎(｡・ω・｡)"
]

SLEEP_RESPONSES = [
    "晚安~你也要好好休息喔(´▽`) ",
    "晚安!祝你今晚有個好夢喔(｡･ω･｡)ﾉ♡ ",
    "哈啊...晚安zzzz..(¦3[▓▓]",
    "{name}晚安~今天也辛苦了✨ ",
    "晚安~{name}今天也很努力了呢(≧∇≦)ﾉ",
    "晚...安...呼...(●ˇ∀ˇ●)"
]

FOOD_RESPONSES = [
    "便當","7-11","麥當勞","炸雞","肯德基","BBQ","河粉","炸物","東南亞料理","炒飯","義大利麵","早餐店","燉飯","永和豆漿","丼飯",
    "鹽水雞","粥","牛排","拉麵","臭豆腐","餛飩","油飯","餃子","沙拉","泡麵","燒臘","小火鍋","壽司","麵包","關東煮","手搖飲",
    "炸魚薯條","炒粿條","pizza","控肉飯","春捲","牛肉麵","排骨飯","咖哩","三明治","烏龍麵","鍋燒意麵","章魚燒","蕎麥麵","湯圓",
    "飯捲","地瓜球","天婦羅","手做漢堡","刈包","肉圓","胡椒餅","水果","麻糬","粽子","月餅"
    ]

TAROT_RESPONSES = load_tarot()
# 1. 設定鬧鐘時間 (例如晚上 22:30)
tw_tz = timezone(timedelta(hours=8))

ALARM_TIME = time(hour=22, minute=30, tzinfo=tw_tz)

ROLE_ID1=1487820279190388900
ROLE_ID2=1487820036541513788
ROLE_ID_book=1496196727412232232


REMIND_TIMES1 = [
    time(hour=8, minute=0, tzinfo=tw_tz),
    time(hour=18, minute=0, tzinfo=tw_tz)
]

REMIND_TIMES2 = [
    time(hour=0, minute=0, tzinfo=tw_tz),
    time(hour=3, minute=0, tzinfo=tw_tz),
    time(hour=6, minute=0, tzinfo=tw_tz),
    time(hour=9, minute=0, tzinfo=tw_tz),
    time(hour=12, minute=0, tzinfo=tw_tz),
    time(hour=15, minute=0, tzinfo=tw_tz),
    time(hour=18, minute=0, tzinfo=tw_tz),
    time(hour=21, minute=0, tzinfo=tw_tz)
]

REMIND_TIMES3 = [
    time(hour=23, minute=30, tzinfo=tw_tz),
    time(hour=0, minute=0, tzinfo=tw_tz)
]

# yt-dlp 設定
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True, # 屏蔽掉那些煩人的 WARNING
    # 關鍵：強制指定只用 Bilibili 的解析器，不要亂跳 YouTube 客戶端
    'allowed_extractors': ['bilibili.*', 'generic'], 
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Origin': 'https://www.bilibili.com',
        'Referer': 'https://www.bilibili.com/',
    },
    # 這裡加入這行，強迫它不要檢查 HTTPS 證書，有時候能繞過某些阻擋
    'nocheckcertificate': True,
}
FFMPEG_OPTIONS = {
    'before_options': (
        '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 '
        '-headers "Referer: https://www.bilibili.com/\r\n'
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36\r\n"'
    ),
    'options': '-vn'
}

def check_queue(ctx):
    """檢查清單並播放下一首的輔助函式"""
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        # 取出下一首
        next_song = queues[ctx.guild.id].pop(0)
        
        # 建立音源 (注意：在 after 函式中無法使用 await，所以這裡需要同步處理或用 loop)
        # 為了簡單起見，我們在 play 主程式中處理，這裡只負責觸發
        coro = play_music(ctx, next_song)
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except:
            pass

async def play_music(ctx, song_data):
    url2 = song_data['url']
    vc = ctx.voice_client
    # 關鍵：不要用 from_probe，改用 FFmpegOpusAudio 或 FFmpegPCMAudio
    # 直接手動指定路徑，並帶入我們寫好的 Headers
    source = discord.FFmpegOpusAudio(
        url2, 
        executable="C:/ffmpeg/bin/ffmpeg.exe", 
        **FFMPEG_OPTIONS
    )
    
    vc.play(source, after=lambda e: check_queue(ctx))
    await ctx.send(f"🎵 正在播放: **{song_data['title']}**")

#async def play_music(ctx, song_info):
#    """實際執行 FFMPEG 播放的函式"""
#    vc = ctx.voice_client
#    url2 = song_info['url']
#    
#    source = await discord.FFmpegOpusAudio.from_probe(
#        url2, executable="C:/ffmpeg/bin/ffmpeg.exe", **FFMPEG_OPTIONS
#    )
#    
    # 播放完畢後，呼叫 check_queue 檢查下一首
#    vc.play(source, after=lambda e: check_queue(ctx))
#    await ctx.send(f"🎵 正在播放: **{song_info['title']}**")

@bot.command()
async def Play(ctx, *, url:str):
    if not ctx.author.voice:
        return await ctx.send("你必須先加入語音頻道！")

    # 連線邏輯
    if ctx.voice_client is None:
        vc = await ctx.author.voice.channel.connect()
    else:
        vc = ctx.voice_client

    async with ctx.typing():
        # 判斷輸入的是不是網址，如果不是，就加上搜尋前綴
        if not url.startswith("https://"):
            query = f"bilisearch1:{url}"
        else:
            query = url

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # 執行搜尋或解析網址
                # 原本的做法 (會卡住心跳)
                # info = ydl.extract_info(query, download=False)

                # 修改後的做法 (在背景執行，不影響心跳)
                loop = asyncio.get_event_loop()
                await asyncio.sleep(random.uniform(1, 3))
                info = await loop.run_in_executor(None, lambda: ydl.extract_info(query, download=False))
                
                # 如果是搜尋結果，info['entries'] 會是一個清單，取第一個
                if 'entries' in info:
                    info = info['entries'][0]
                
                # 這裡抓取 duration 並存入 song_data
                duration_str = parse_duration(info.get('duration'))
                song_data = {
                    'url': info['url'], 
                    'title': info['title'],
                    'duration': duration_str # 存入格式化後的時長
                }
            except Exception as e:
                return await ctx.send(f"搜尋出錯或找不到影片：{e}")

        # 之後的播放與 Queue 邏輯保持不變...
        if ctx.guild.id not in queues:
            queues[ctx.guild.id] = []

        if vc.is_playing() or vc.is_paused():
            queues[ctx.guild.id].append(song_data)
            await ctx.send(f"✅ 已加入待播清單: **{info['title']}**`({duration_str})`")
        else:
            await play_music(ctx, song_data)

# --- 新增功能：暫停/恢復 ---
@bot.command()
async def Pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ 已暫停播放")

@bot.command()
async def Resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ 繼續播放")

# --- 新增功能：跳過 ---
@bot.command()
async def Skip(ctx):
    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
        ctx.voice_client.stop() # stop 會自動觸發 after 參數，進而播放下一首
        await ctx.send("⏭️ 已跳過當前歌曲")

# --- 新增功能：查詢清單 ---
@bot.command(name="Q")
async def queue_list(ctx):
    if ctx.guild.id not in queues or not queues[ctx.guild.id]:
        return await ctx.send("目前的待播清單是空的。")
    
    msg = "📋 **待播清單:**\n"
    for i, song in enumerate(queues[ctx.guild.id], 1):
        msg += f"{i}. {song['title']}`[{song['duration']}]`\n"
    await ctx.send(msg)

# --- 新增功能：刪除指定曲目 ---
@bot.command()
async def Remove(ctx, index: int):
    try:
        removed = queues[ctx.guild.id].pop(index - 1)
        await ctx.send(f"🗑️ 已移除: **{removed['title']}**")
    except:
        await ctx.send("找不到該編號的歌曲。")

# --- 新增功能：調整順序 ---
@bot.command()
async def Move(ctx, old_index: int, new_index: int):
    try:
        song = queues[ctx.guild.id].pop(old_index - 1)
        queues[ctx.guild.id].insert(new_index - 1, song)
        await ctx.send(f"↕️ 已將 **{song['title']}** 移動到第 {new_index} 位")
    except:
        await ctx.send("調整順序失敗，請檢查編號。")

@bot.command()
async def Leave(ctx):
    if ctx.voice_client:
        queues[ctx.guild.id] = [] # 清空清單
        await ctx.voice_client.disconnect()
        await ctx.send("👋 已離開頻道並清空清單。")
    else:
        await ctx.send("我目前不在任何語音頻道中。")

##定時提醒part

@tasks.loop(time=REMIND_TIMES1)
async def daily_ritual1():
    channel = bot.get_channel(1487820679738032319) # 記得換成你的頻道 ID
    if channel:
        await channel.send(f"<@&{ROLE_ID1}>叮咚！有人跟我說他有事要做 ٩(｡・ω・｡)و\n我來看看他做的怎樣了")

@tasks.loop(time=REMIND_TIMES2)
async def daily_ritual2():
    channel = bot.get_channel(1487820679738032319) # 記得換成你的頻道 ID
    if channel:
        await channel.send(f"<@&{ROLE_ID2}>嗶嗶嗶！你好阿~現在是休息時間~\n記得喝水吃飯上廁所啊ლ⁠(⁠・⁠﹏⁠・⁠ლ⁠)")

@tasks.loop(time=REMIND_TIMES3)
async def sleep_alarm():
    channel = bot.get_channel(1487820679738032319) # 記得換成你的頻道 ID
    if channel:
        time1 = datetime.now(tw_tz).strftime("%H:%M")
        await channel.send(f"<@&1500387079065047171> \n⏰ 嗡嗡嗡嗡\n現在時間{time1}\n12點睡覺小組洗澡了沒？\n躺在床上了沒？\n誰還在活網？\n糾察隊嗶嗶嗶⁠)")

@tasks.loop(time=ALARM_TIME)
async def scheduled_alarm():
    # 取得今天的星期幾 (0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun)
    today = datetime.now(tw_tz).weekday()
    
    # 判斷是否為週一 (0)、週三 (2) 或週五 (4)
    if today in [0, 2, 4]:
        channel = bot.get_channel(1487820679738032319)
        if channel:
            # 轉換數字變成中文方便閱讀
            day_map = {0: "一", 2: "三", 4: "五"}
            day = day_map[today]
            await channel.send(f"🔔 叮叮叮！現在是週{day}晚上10:30，召喚<@&{ROLE_ID_book}>們提醒希姆備考喔(,,・ω・,,)")

# 準備工作：確保機器人連線後才開始計時
@daily_ritual1.before_loop
async def before_daily_ritual1():
    await bot.wait_until_ready()

@daily_ritual2.before_loop
async def before_daily_ritual2():
    await bot.wait_until_ready()

@scheduled_alarm.before_loop
async def before_alarm():
    await bot.wait_until_ready()

##匿名投稿區
ADMIN_CHANNEL_ID =1488105547063492681
PUBLIC_CHANNEL_ID =1487713981903667311

@bot.event
async def on_message(message):
    # 讓指令功能繼續運作 (這行一定要加，否則音樂指令會失效！)
    await bot.process_commands(message)

    # 如果是頻道 1 的新訊息 (且是投稿格式)
    if message.channel.id == ADMIN_CHANNEL_ID and "📩 **新投稿：**\n" in message.content:
        await message.add_reaction("✅")
        await message.add_reaction("❌")
    
    if message.author == bot.user:
        return
    
    if bot.user.mentioned_in(message) and "早安" in message.content:
        # 準備回話清單
        reply_text = random.choice(MORNING_RESPONSES).format(name=message.author.display_name)
        await message.reply(reply_text)
    
    if bot.user.mentioned_in(message) and "晚安" in message.content:
        # 準備回話清單
        reply_text = random.choice(SLEEP_RESPONSES).format(name=message.author.display_name)
        await message.reply(reply_text)

    if bot.user.mentioned_in(message) and "吃什麼" in message.content:
        # 準備回話清單
        reply_text = random.choice(FOOD_RESPONSES)
        await message.reply(reply_text)
    
    if bot.user.mentioned_in(message) and "運勢" in message.content:
        card_key = random.choice(list(TAROT_RESPONSES.keys()))
        is_upright = random.choice([True, False])
        advise_key = "advise1" if is_upright else "advise2"
        upright= "正位" if is_upright else "逆位"
        # 準備回話清單
    #   reply_text = random.choice(TAROT_RESPONSES).format(name=message.author.display_name)
        reply_text = TAROT_RESPONSES[card_key]["name"]+" "+upright+" "+"\n"+TAROT_RESPONSES[card_key][advise_key].format(name=message.author.display_name)
        await message.reply(reply_text)
    
    if bot.user.mentioned_in(message) and "塔羅牌" in message.content:
        # 準備回話清單
        reply_text = ""
        for i in range(77):
            keys = list(TAROT_RESPONSES.keys())
            reply_text +=keys[i] + " " + TAROT_RESPONSES[keys[i]]["name"] + "\n"
        await message.reply(reply_text)


@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id: return
    if payload.channel_id != ADMIN_CHANNEL_ID: return
    
    # 取得頻道與訊息物件
    channel1 = bot.get_channel(payload.channel_id)
    try:
        message = await channel1.fetch_message(payload.message_id)
    except: return

    # 判斷點擊的表情
    if str(payload.emoji) == "✅":
        channel2 = bot.get_channel(PUBLIC_CHANNEL_ID)
        # 提取內容並發送 (使用 Embed 比較精緻)
        content = message.content.replace("📩 **新投稿：**\n", "")
        embed = discord.Embed(title="📜 匿名投稿", description=content+"\n\n歡迎各位匿名投稿(´▽`)https://genie2007ouo.pythonanywhere.com/ \n投稿將在人工審核(管理員們)後由胡亓發布在這裡", color=0xD3A4FF)
        await channel2.send(embed=embed)
        await message.delete() # 審核完刪除單子
        
    elif str(payload.emoji) == "❌":
        await message.delete() # 不通過直接刪除

##清訊息(用戶)
@bot.command()
@commands.has_permissions(manage_messages=True) # 確保只有有權限的人能用
async def clean(ctx, member: discord.Member, amount: int = 100):
    
    def is_member(m):
        return m.author == member

    async with ctx.typing():
        # purge 會執行過濾邏輯：只刪除符合 is_member 條件的訊息
        deleted = await ctx.channel.purge(limit=amount, check=is_member)
    
    await ctx.send(f"🧹 已清理 {member.display_name} 在此頻道的 {len(deleted)} 則訊息。", delete_after=5)

# 錯誤處理：如果沒權限的人亂玩指令
@clean.error
async def clean_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 你沒有「管理訊息」的權限，不能使用這個指令喔！")

##清訊息(全頻)
@bot.command()
@commands.has_permissions(manage_messages=True) # 限制只有管理員能用
async def purge(ctx, amount: int):
    """
    用法：!purge <數量>
    例如：!purge 50 (直接刪除最近的 50 則訊息)
    """
    if amount <= 0:
        return await ctx.send("請輸入大於 0 的數字喔！")
    
    # 為了安全，我們可以設定一個上限（例如一次最多刪 100 則）
    if amount > 100:
        await ctx.send("⚠️ 安全起見，一次最多只能刪除 100 則訊息。正在為你刪除前 100 則...")
        amount = 100

    async with ctx.typing():
        # 直接執行刪除
        deleted = await ctx.channel.purge(limit=amount)
    
    # 發送成功訊息，並在 3 秒後自動刪除，保持頻道乾淨
    await ctx.send(f"🧹 已成功清理 {len(deleted)} 則訊息！", delete_after=3)

# 錯誤處理：如果參數不是數字
@purge.error
async def purge_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send("❌ 請輸入正確的數字，例如：`!purge 20`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 你沒有權限執行此指令。")

##遊客身分組
# --- 修改處：設定你的身分組 ID ---
ROLE_A_ID = 1479927475965526127  # 目標身分組 (例如：正式成員)
ROLE_B_ID = 1490237881636094065  # 暫時身分組 (例如：未驗證)
ROLE_C_ID = 1500172980980809919 #沒自介身分組
ROLE_D_ID = 1500173550714224801 #有自介身分組
# 1. 自動監聽：身分組變動時觸發
@bot.event
async def on_member_update(before, after):
    role_a = after.guild.get_role(ROLE_A_ID)
    role_b = after.guild.get_role(ROLE_B_ID)
    role_c = after.guild.get_role(ROLE_C_ID)
    role_d = after.guild.get_role(ROLE_D_ID)
    if not role_a or not role_b or not role_c or not role_d:
        return

    # 邏輯：如果新獲得了 A，就移除 B
    if role_a not in before.roles and role_a in after.roles:
        if role_b in after.roles:
            await after.remove_roles(role_b, reason="已獲得 A 身分組，自動移除 B")
            print(f"✅ 已為 {after.display_name} 移除 B 身分組")

    # 邏輯：如果失去了 A，就補回 B (看你是否需要這個後備)
    if role_a in before.roles and role_a not in after.roles:
        if role_b not in after.roles:
            await after.add_roles(role_b, reason="失去 A 身分組，自動補回 B")
            print(f"ℹ️ 已為 {after.display_name} 補回 B 身分組")

    if role_d not in before.roles and role_d in after.roles:
        if role_c in after.roles:
            await after.remove_roles(role_c, reason="已獲得 d 身分組，自動移除 c")
            print(f"✅ 已為 {after.display_name} 移除 c 身分組")        
    
    # 邏輯：如果失去了自介，就補回 C
    if role_d not in before.roles and role_d not in after.roles:
        if role_c not in after.roles:
            await after.add_roles(role_c, reason="失去自介，自動補回 C")
            print(f"ℹ️ 已為 {after.display_name} 補回 C 身分組")

# 2. 手動指令：一鍵校正全伺服器成員
@bot.command()
@commands.has_permissions(manage_roles=True)
async def sync_roles(ctx):
    """加強版：強制讀取成員並校正身分組"""
    role_a = ctx.guild.get_role(ROLE_A_ID)
    role_b = ctx.guild.get_role(ROLE_B_ID)
    role_c = ctx.guild.get_role(ROLE_C_ID)
    role_d = ctx.guild.get_role(ROLE_D_ID)
    
    if not role_a or not role_b or not role_c or not role_d:
        return await ctx.send("❌ 找不到指定的身分組 ID，請確認代碼最上方的 ID 是否正確。")

    await ctx.send("🔍 正在同步成員資料並開始校正，請稍候...")

    async with ctx.typing():
        # 關鍵修正：如果成員清單為空，強制請求下載成員資料
        if not ctx.guild.chunked:
            await ctx.guild.chunk()

        success_count = 0
        fail_count = 0
        
        for member in ctx.guild.members:
            if member.bot: continue # 略過機器人
            
            try:
                # 狀況 1：沒有 A 且沒有 B -> 補上 B
                if role_a not in member.roles and role_b not in member.roles:
                    await member.add_roles(role_b, reason="一鍵校正：補上 B")
                    success_count += 1                
                elif role_c not in member.roles and role_d not in member.roles:
                    await member.add_roles(role_c, reason="一鍵校正：補上 C")
                    success_count += 1
                # 狀況 2：已有 A 卻還有 B -> 移除 B
                elif role_a in member.roles and role_b in member.roles:
                    await member.remove_roles(role_b, reason="一鍵校正：移除多餘 B")
                    success_count += 1
                elif role_c in member.roles and role_d in member.roles:
                    await member.remove_roles(role_c, reason="一鍵校正：移除多餘 C")
                    success_count += 1
            except discord.Forbidden:
                # 如果權限不足（階層不夠高），會跳到這裡
                fail_count += 1
            except Exception as e:
                print(f"處理 {member.display_name} 時發生錯誤: {e}")

    await ctx.send(f"✅ 校正完成！\n- 成功更新：{success_count} 位\n- 失敗（權限不足）：{fail_count} 位")

# 3. 自動監聽：當有新成員加入伺服器時觸發
@bot.event
async def on_member_join(member):
    # 取得 B 身分組物件
    role_b = member.guild.get_role(ROLE_B_ID)
    role_c = member.guild.get_role(ROLE_C_ID)
    if role_b:
        try:
            # 為新成員加上 B 身分組
            await member.add_roles(role_b, reason="新人進群，自動給予初始身分組")
            print(f"🐣 新成員 {member.display_name} 已自動獲得 B 身分組")
            
            # (選填) 也可以順便在審核頻道或歡迎頻道發個通知
            # welcome_channel = bot.get_channel(你的頻道ID)
            # await welcome_channel.send(f"歡迎 {member.mention} 來到伺服器！請記得完成驗證喔～")
            
        except discord.Forbidden:
            print(f"❌ 權限不足！無法為 {member.display_name} 加上身分組。請檢查機器人權限順序。")
        except Exception as e:
            print(f"❌ 發生錯誤：{e}")
    elif role_c:
        try:
            # 為新成員加上 C 身分組
            await member.add_roles(role_c, reason="新人進群，自動給予初始身分組")
            print(f"🐣 新成員 {member.display_name} 已自動獲得 C 身分組")
            
            # (選填) 也可以順便在審核頻道或歡迎頻道發個通知
            # welcome_channel = bot.get_channel(你的頻道ID)
            # await welcome_channel.send(f"歡迎 {member.mention} 來到伺服器！請記得完成驗證喔～")
            
        except discord.Forbidden:
            print(f"❌ 權限不足！無法為 {member.display_name} 加上身分組。請檢查機器人權限順序。")
        except Exception as e:
            print(f"❌ 發生錯誤：{e}")

##定時重啟
@bot.command()
@commands.has_permissions(administrator=True)
async def restart(ctx):
    """手動強制重啟機器人"""
    await ctx.send("🔄 正在執行系統重啟，請稍候...")
    # 關閉所有的 loop 任務
    daily_ritual1.cancel()
    daily_ritual2.cancel()
    scheduled_alarm.cancel()
    sleep_alarm.cancel()
    # 執行重啟
    os.execv(sys.executable, ['python'] + sys.argv)

# 設定重啟時間，建議選在沒人使用的時段，例如凌晨 4 點
REBOOT_TIME = [time(hour=4, minute=0, tzinfo=tw_tz)]

@tasks.loop(time=REBOOT_TIME)
async def auto_reboot():
    print("⏰ 觸發定時重啟任務...")
    # 如果有正在播放音樂，可以先發送通知
    # 執行重啟
    os.execv(sys.executable, ['python'] + sys.argv)

@auto_reboot.before_loop
async def before_reboot():
    await bot.wait_until_ready()

# 記得在 on_ready 啟動它
@bot.event
async def on_ready():
    print(f"目前登入身份 --> {bot.user}")
    
    # 檢查任務是否已在執行，避免重複啟動
    tasks_to_start = [auto_reboot, daily_ritual1,daily_ritual2, scheduled_alarm, sleep_alarm]
    for task in tasks_to_start:
        if not task.is_running():
            task.start()

bot.run(TOKEN)