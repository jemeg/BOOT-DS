import discord
from discord.ext import commands
import asyncio
import json
import os
from keep_alive import keep_alive

# إعدادات البوت
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# قائمة القوانين (يمكنك تعديلها لاحقاً)
RULES = [
    "📜 **القانون الأول**: احترام جميع الأعضاء",
    "📜 **القانون الثاني**: ممنوع إرسال روابط غير لائقة", 
    "📜 **القانون الثالث**: لا تكرار الرسائل",
    "📜 **القانون الرابع**: استخدام اللغة اللائقة فقط",
    "📜 **القانون الخامس**: عدم نشر معلومات شخصية"
]

@bot.event
async def on_ready():
    print(f'البوت جاهز! {bot.user}')
    print(f'البوت في {len(bot.guilds)} سيرفر')

@bot.event
async def on_voice_state_update(member, before, after):
    # التحقق إذا كان العضو دخل روم صوتي
    if before.channel is None and after.channel is not None:
        # إنشاء رسالة ثلاثية الأبعاد للقوانين
        embed = discord.Embed(
            title="🎮 **قوانين السيرفر** 🎮",
            description=f"مرحباً {member.mention} في روم **{after.channel.name}**!\n\nيرجى الالتزام بالقوانين التالية:",
            color=discord.Color.blue()
        )
        
        # إضافة القوانين
        for rule in RULES:
            embed.add_field(name="📋", value=rule, inline=False)
        
        # إضافة صورة ثلاثية الأبعاد (يمكنك تغيير الرابط)
        embed.set_image(url="https://i.imgur.com/3D-rules-example.png")
        embed.set_footer(text=f"تم الإرسال بواسطة {bot.user.name}")
        embed.set_thumbnail(url=member.avatar.url if member.avatar else bot.user.avatar.url)
        
        # إرسال الرسالة في روم القوانين أو روم عام
        rules_channel = discord.utils.get(member.guild.text_channels, name="قوانين")
        if not rules_channel:
            rules_channel = discord.utils.get(member.guild.text_channels, name="general")
        if not rules_channel:
            rules_channel = member.guild.text_channels[0]  # أول روم نصي
            
        await rules_channel.send(embed=embed)
        
        # إرسال رسالة ترحيب في الروم الصوتي نفسه
        if after.channel and after.channel.name:
            welcome_embed = discord.Embed(
                title=f"🎉 أهلاً بك في {after.channel.name}!",
                description=f"{member.mention} انضم للروم الصوتي",
                color=discord.Color.green()
            )
            welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else bot.user.avatar.url)
            
            # البحث عن روم نصي بنفس اسم الروم الصوتي
            text_channel = discord.utils.get(member.guild.text_channels, name=after.channel.name.lower())
            if text_channel:
                await text_channel.send(embed=welcome_embed)

@bot.command()
async def قوانين(ctx):
    """عرض القوانين"""
    embed = discord.Embed(
        title="📜 **قوانين السيرفر**",
        description="قوانين السيرفر:",
        color=discord.Color.gold()
    )
    
    for rule in RULES:
        embed.add_field(name="📋", value=rule, inline=False)
    
    embed.set_footer(text=f"طلب بواسطة {ctx.author.name}")
    await ctx.send(embed=embed)

@bot.command()
async def تحديث_القوانين(ctx, *, new_rules: str = None):
    """تحديث القوانين (للمشرفين فقط)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ هذا الأمر متاح للمشرفين فقط!")
        return
    
    if new_rules:
        # هنا يمكنك حفظ القوانين الجديدة في ملف أو قاعدة بيانات
        await ctx.send("✅ تم تحديث القوانين بنجاح!")
    else:
        await ctx.send("❌ يرجى كتابة القوانين الجديدة بعد الأمر")

# تشغيل البوت
keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))
