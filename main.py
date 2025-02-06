import discord
from discord.ext import commands
from datetime import timedelta
import os

# Intents 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True  # 멤버 정보 접근을 위해 추가

# 봇의 접두사 설정
bot = commands.Bot(command_prefix='!', intents=intents)

# 욕설 리스트와 그에 따른 처벌 및 메시지
penalties = {
    1: {
        'words': ['씨발', '시발', '개새끼', '병신', '미친놈', '미친년', '니거', '등신'],
        'duration': 180,
        'message': '경고: 부적절한 언어를 사용하셨습니다. 3분 타임아웃이 적용됩니다.'
    },
    2: {
        'words': ['운지', '노무현', '고아년', '니거'],
        'duration': 900,
        'message': '심각한 경고: 매우 부적절한 언어를 사용하셨습니다. 15분 타임아웃이 적용됩니다.'
    }
}

# 처벌 보고를 보낼 채널 ID
report_channel_id = 1336609729409187912

@bot.event
async def on_ready():
    print(f'✅ {bot.user}로 로그인했습니다.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    member = message.guild.get_member(message.author.id)
    if not member:
        return

    for penalty_level, penalty in penalties.items():
        if any(word in message.content for word in penalty['words']):
            until_time = discord.utils.utcnow() + timedelta(seconds=penalty['duration'])
            await message.author.timeout(until=until_time, reason=penalty['message'])
            await message.channel.send(f"⚠ {message.author.mention}, {penalty['message']} {penalty['duration'] // 60}분 동안 타임아웃됩니다.")
            
            report_channel = bot.get_channel(report_channel_id)
            if report_channel:
                bad_word = next(word for word in penalty['words'] if word in message.content)
                await report_channel.send(f"🚨 처벌 대상자: {message.author.mention}\n욕설: `{bad_word}`\n처벌: {penalty['message']}")

            break

    await bot.process_commands(message)

TOKEN = os.getenv("BOT_TOKEN")

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ BOT_TOKEN이 설정되지 않았습니다. 환경 변수를 확인하세요!")


