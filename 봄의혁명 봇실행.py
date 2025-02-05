import discord
from discord.ext import commands
from datetime import timedelta

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

 # 추방할 서버의 ID와 이름으로 변경하세요.
}

@bot.event
async def on_ready():
    print(f'{bot.user}로 로그인했습니다.')

@bot.event
async def on_message(message):
    # 봇이 보낸 메시지는 무시
    if message.author == bot.user:
        return

    # 특정 서버에서 추방 처리
    for guild_id, guild_name in restricted_guilds.items():
        if guild_id in [guild.id for guild in message.author.guilds]:
            await message.guild.kick(message.author)
            await message.channel.send(f"{message.author.mention}님은 `{guild_name}` 유저로 판단, 자동 차단되셨습니다. 만약 해당 처벌에 이의가 있으실 경우 부계정을 통하여 본 서버에 가입 후, 서버장 DM을 통해 연락 바랍니다.")

            # 추방 기록 보고
            report_channel = bot.get_channel(report_channel_id)
            await report_channel.send(f"처벌 대상자: {message.author.mention}\n처벌: 자동 차단 (`{guild_name}` 유저 판정)")

            return  # 메시지 처리 중단

    # 욕설 체크 및 처벌 적용
    for penalty_level, penalty in penalties.items():
        if any(word in message.content for word in penalty['words']):
            await message.author.timeout(timedelta(seconds=penalty['duration']), reason=penalty['message'])
            await message.channel.send(f"{message.author.mention}님, {penalty['message']} {penalty['duration'] // 60}분 동안 타임아웃됩니다.")
            
            # 처벌 보고
            report_channel = bot.get_channel(report_channel_id)
            bad_word = next(word for word in penalty['words'] if word in message.content)
            await report_channel.send(f"처벌 대상자: {message.author.mention}\n욕설: `{bad_word}`\n처벌: {penalty['message']}")
            break

    # 다른 명령어 처리
    await bot.process_commands(message)

# 봇 토큰으로 로그인
bot.run('TOKEN')
