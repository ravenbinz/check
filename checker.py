import discord
from discord.ext import commands
import os
import re
from bs4 import BeautifulSoup
import requests

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

if not os.path.exists("checker"):   
    os.makedirs("checker")

TOKEN = 'MTI4NDQ4OTMyMjQxODE0NzM0OQ.GTMZR8.CVgWq7MWo5DQhTkIcZzqhDG6ZxTrBeBZGyy420'

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id != 1276961272495214704:
        return

    if message.attachments:
        for attachment in message.attachments:
            if attachment.filename.endswith('.txt'):
                file_path = os.path.join("checker", attachment.filename)
                await attachment.save(file_path)

                result = check_netflix(file_path)
                if result:
                    response = f"Netflix cookie is valid!\n"
                    response += f"Plan: {result['plan']}\n"
                    response += f"ExtraMember: {result['extra']}\n"
                    response += f"Country: {result['country']}"
                else:
                    response = "Netflix cookie is invalid."
                    os.remove(file_path)
                
                await message.author.send(response)

                await message.delete()
            else:
                await message.delete()
                await message.author.send("Only text files (.txt) are allowed as attachments.")
                return


    else: 
        await message.delete()
        await message.author.send("Only text files (.txt) are allowed in checker public!")
        return

    await bot.process_commands(message)


def check_netflix(path):
    cookies = {}
    l = []
    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            if any(keyword in line for keyword in ["NetflixId", "SecureNetflixId"]):
                l.append(line)
                cookie_parts = re.split(r'\t', line.strip())
                name, value = cookie_parts[5], cookie_parts[6]
                cookies[name] = value

    url = "https://www.netflix.com/YourAccount"

    response = requests.get(url, cookies=cookies)
    if "/account" in response.url:
        html = response.text

        soup = BeautifulSoup(html, 'lxml')

        plan_tag = soup.find('h3', {'data-uia': 'account-overview-page+membership-card+title'})
        if plan_tag:
            plan_text = plan_tag.get_text(separator=" ", strip=True)
            plan_parts = plan_text.split(' ', 1)
            plan = plan_parts[0]
            if len(plan_parts) > 1:
                plan += ' ' + plan_parts[1]
        else:
            plan = "Free"

        extra = "manage-extra-members" in html or "invite-extra-members" in html

        if "currentCountry" in html:
            start_index = html.find("currentCountry") + len("currentCountry") + 3
            end_index = html.find('"', start_index)
            country_text = html[start_index:end_index]

        payment_method = "Third party"
        if "VISA.png" in html:
            payment_method = "Visa"
        elif "MASTERCARD.png" in html:
            payment_method = "Mastercard"
        elif "PAYPAL.png" in html:
            payment_method = "Paypal"
        elif "Xfinity" in html:
            payment_method = "Xfinity"
        elif "T-Mobile" in html:
            payment_method = "T-Mobile"
        else:
            payment_method = "Unknown"

        lines = l
        return {
            "plan": plan,
            "extra": extra,
            "country": country_text,
            "payment_method": payment_method,
            "lines": lines
        }
    else:
        return False


bot.run(TOKEN)
