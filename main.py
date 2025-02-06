import discord
from discord.ext import commands
from datetime import timedelta
import os
import random
import asyncio

# 봇 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True  # 멤버 정보 접근을 위해 추가

bot = commands.Bot(command_prefix="!", intents=intents)

# 인증 관련 변수
verification_channel_id = 1337078782196187168  # 인증 채널 ID
verified_role_id = 1334407922628952076  # 인증 후 부여할 역할 ID
verification_codes = {}  # 인증 코드 저장

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

# 인증 버튼을 제공할 채널 ID 및 역할 ID
OAUTH2_URL = "https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=identify+guilds&response_type=code&redirect_uri=YOUR_REDIRECT_URI"

class VerificationButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # 인증 버튼 클릭 시 DM으로 인증 코드 전송
        await interaction.response.send_message(f"입국심사소 출입허가를 위해 DM을 확인해주세요.", ephemeral=True)
        user = interaction.user
        code = str(random.randint(100000, 999999))  # 6자리 인증 코드 생성
        verification_codes[user.id] = {'code': code, 'time': asyncio.get_event_loop().time() + 300}  # 5분 유효

        # 사용자에게 인증 코드 전송
        await user.send(f"인증 코드: {code}")

@bot.event
async def on_ready():
    print(f'✅ {bot.user}로 로그인했습니다.')
    channel = bot.get_channel(verification_channel_id)
    if channel:
        await channel.send("입국심사소 출입허가를 진행하려면 아래 버튼을 눌러주세요.", view=VerificationButton())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    member = message.guild.get_member(message.author.id)
    if not member:
        return

    # 욕설 필터링 및 타임아웃 적용
    for penalty_level, penalty in penalties.items():
        if any(word in message.content for word in penalty['words']):
            until_time = discord.utils.utcnow() + timedelta(seconds=penalty['duration'])
            await message.author.timeout(until=until_time, reason=penalty['message'])
            await message.channel.send(f"⚠ {message.author.mention}, {penalty['message']} {penalty['duration'] // 60}분 동안 타임아웃됩니다.")
            
            # 보고 채널로 전송
            report_channel = bot.get_channel(1336609729409187912)  # 처벌 보고를 보낼 채널 ID
            if report_channel:
                bad_word = next(word for word in penalty['words'] if word in message.content)
                await report_channel.send(f"🚨 처벌 대상자: {message.author.mention}\n욕설: `{bad_word}`\n처벌: {penalty['message']}")

            break

    # 인증 코드 검증
    if message.channel.id == verification_channel_id:
        user_id = message.author.id
        code_sent = message.content.strip()

        if user_id in verification_codes:
            stored_code = verification_codes[user_id]['code']
            expiry_time = verification_codes[user_id]['time']

            # 인증 코드 검증
            if code_sent == stored_code:
                # 코드가 맞으면 역할 부여
                member = message.guild.get_member(user_id)
                if member:
                    role = message.guild.get_role(verified_role_id)
                    if role and role not in member.roles:
                        await member.add_roles(role)
                        await message.channel.send(f"{message.author.mention}님 입국심사소 출입허가 완료! 입국심사 자격이 부여되었습니다.")
                    
                    # 인증 코드 삭제
                    del verification_codes[user_id]
                else:
                    await message.channel.send(f"{message.author.mention}님을 서버에서 찾을 수 없습니다.")
            else:
                await message.channel.send(f"{message.author.mention}님, 인증 코드가 일치하지 않습니다. 다시 시도해주세요.")
            
            # 인증 코드가 만료되었으면 삭제
            if asyncio.get_event_loop().time() > expiry_time:
                del verification_codes[user_id]
                await message.channel.send(f"{message.author.mention}님의 인증 코드가 만료되었습니다. 다시 요청해주세요.")

            # 인증 완료 후 버튼을 다시 보내기
            channel = bot.get_channel(verification_channel_id)
            if channel:
                await channel.send("입국심사소 출입허가를 진행하려면 아래 버튼을 눌러주세요.", view=VerificationButton())

    # 기본적으로 on_message에서 명령어도 처리하도록
    await bot.process_commands(message)

TOKEN = os.getenv("BOT_TOKEN")
bot.run(TOKEN)


