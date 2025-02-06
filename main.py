import discord
from discord.ext import commands
from datetime import timedelta
import os

# Intents 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True  # 서버 관련 이벤트 수신 허용

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

# 특정 서버 IDs 및 이름 매핑
restricted_guilds = {
    783235160921341962: "장애당",
    1256967198350643332: "정화당"
}

@bot.event
async def on_ready():
    print(f'✅ {bot.user}로 로그인했습니다.')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # 메시지를 보낸 사용자의 서버 목록 확인 (Member 객체로 변환)
    member = message.guild.get_member(message.author.id)
    if not member:
        return

    # 특정 서버에서 추방 처리
    for guild_id, guild_name in restricted_guilds.items():
        if guild_id in [g.id for g in bot.guilds]:  # 봇이 있는 서버와 비교
            await message.guild.kick(member, reason=f"{guild_name} 유저로 판정됨")
            await message.channel.send(f"{message.author.mention}님은 `{guild_name}` 유저로 판단되어 자동 차단되었습니다.")

            # 추방 기록 보고
            report_channel = bot.get_channel(report_channel_id)
            if report_channel:
                await report_channel.send(f"⚠ 처벌 대상자: {message.author.mention}\n처벌: 자동 차단 (`{guild_name}` 유저 판정)")

            return  # 메시지 처리 중단

    # 욕설 체크 및 처벌 적용
    for penalty_level, penalty in penalties.items():
        if any(word in message.content for word in penalty['words']):
            until_time = discord.utils.utcnow() + timedelta(seconds=penalty['duration'])  # UTC 기준 타임아웃 시간 계산
            await message.author.timeout(until=until_time, reason=penalty['message'])
            await message.channel.send(f"⚠ {message.author.mention}, {penalty['message']} {penalty['duration'] // 60}분 동안 타임아웃됩니다.")
            
            # 처벌 보고
            report_channel = bot.get_channel(report_channel_id)
            if report_channel:
                bad_word = next(word for word in penalty['words'] if word in message.content)
                await report_channel.send(f"🚨 처벌 대상자: {message.author.mention}\n욕설: `{bad_word}`\n처벌: {penalty['message']}")

            break  # 첫 번째로 감지된 욕설에 대해서만 처리

    # 명령어 처리 (여기까지 오면 bot.process_commands 실행됨)
    await bot.process_commands(message)

# 환경 변수에서 봇 토큰 가져오기
TOKEN = os.getenv("BOT_TOKEN")

# 봇 실행
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ BOT_TOKEN이 설정되지 않았습니다. 환경 변수를 확인하세요!")


