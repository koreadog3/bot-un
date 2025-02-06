import discord
from discord.ext import commands
from datetime import timedelta
import os
import threading
from flask import Flask, redirect, request
import requests

# Flask 서버 설정
app = Flask(__name__)
app.secret_key = os.urandom(24)

OAUTH2_CLIENT_ID = "1297501772339871755"
OAUTH2_CLIENT_SECRET = os.getenv("OAUTH2_CLIENT_SECRET")  # 환경 변수에서 클라이언트 비밀키 가져오기
OAUTH2_REDIRECT_URI = "https://bot-un.koyeb.app/oauth2/callback"
OAUTH2_URL = f"https://discord.com/oauth2/authorize?client_id=1297501772339871755&scope=identify+guilds&response_type=code&redirect_uri=https://bot-un.koyeb.app/oauth2/callback"

# 인증 후 받은 'code'를 이용하여 액세스 토큰을 요청하는 함수
def get_access_token(code):
    data = {
        'client_id': OAUTH2_CLIENT_ID,
        'client_secret': OAUTH2_CLIENT_SECRET,  # 클라이언트 비밀키 사용
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': OAUTH2_REDIRECT_URI
    }
    response = requests.post("https://discord.com/api/oauth2/token", data=data)
    return response.json().get('access_token')

@app.route('/')
def home():
    return "OAuth2 인증 서버"

# OAuth2 콜백 처리
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "인증 실패, 코드가 제공되지 않았습니다.", 400
    
    access_token = get_access_token(code)
    if access_token:
        # 액세스 토큰을 이용해 Discord API를 통해 유저 정보를 가져옴
        user_info = requests.get(
            "https://discord.com/api/v10/users/@me", 
            headers={"Authorization": f"Bearer {access_token}"}
        ).json()
        
        username = user_info['username']
        user_id = user_info['id']
        
        # 봇에서 해당 유저에게 역할을 부여하는 로직 추가
        guild = bot.get_guild(YOUR_GUILD_ID)
        member = guild.get_member(int(user_id))
        if member:
            verified_role = guild.get_role(verified_role_id)
            if verified_role not in member.roles:
                await member.add_roles(verified_role)
                return f"✅ {username}님, 인증이 완료되어 역할이 부여되었습니다!", 200
        return f"회원 {username}을 찾을 수 없습니다.", 404
    return "인증 실패", 400

# Flask 서버를 별도의 스레드에서 실행하는 함수
def run_flask():
    app.run(host='0.0.0.0', port=5000)

# Discord 봇 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True  # 멤버 정보 접근을 위해 추가

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

# 인증 버튼을 제공할 채널 ID 및 역할 ID
verification_channel_id = 1337059669021167748  # 인증 채널 ID
verified_role_id = 1334407922628952076  # 인증 후 부여할 역할 ID

OAUTH2_URL = "https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=identify+guilds&response_type=code&redirect_uri=https://bot-un.koyeb.app/oauth2/callback
"

class VerificationButton(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="인증하기", style=discord.ButtonStyle.green)
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"국경검문소에 접근하려면 [여기]({OAUTH2_URL})를 클릭하세요!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ {bot.user}로 로그인했습니다.')
    channel = bot.get_channel(verification_channel_id)
    if channel:
        await channel.send("국경접근을 위해 아래 버튼을 눌러주세요.", view=VerificationButton())

@bot.event
async def on_member_update(before, after):
    """OAuth2 인증 후 특정 역할 부여"""
    guild = after.guild
    role = guild.get_role(verified_role_id)

    if role and role not in after.roles:
        await after.add_roles(role)
        print(f"✅ {after.name}님에게 국경접근권한을 부여했습니다.")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    member = message.guild.get_member(message.author.id)
    if not member:
        return

    for guild_id, guild_name in restricted_guilds.items():
        if guild_id in [g.id for g in bot.guilds]:
            await message.guild.kick(member, reason=f"{guild_name} 유저로 판정됨")
            await message.channel.send(f"{message.author.mention}님은 `{guild_name}` 유저로 판단되어 자동 차단되었습니다.")

            report_channel = bot.get_channel(report_channel_id)
            if report_channel:
                await report_channel.send(f"⚠ 처벌 대상자: {message.author.mention}\n처벌: 자동 차단 (`{guild_name}` 유저 판정)")

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

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    bot.run(TOKEN)

