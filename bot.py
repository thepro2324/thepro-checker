import discord
from discord import app_commands
import json
import os

# קביעת הרשאות בוט
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# קבועים עבור מזהי רולים שביקשת
ROLE_MANAGER_ID = 1474024190905680085  # רול מנהל עבור add_stock
ROLE_FGEN_ID = 1557079492701192283     # רול FGEN עבור gen

# קובץ לשמירת המלאי מקומית
STOCK_FILE = "stock.json"

# רשימת הקטגוריות המלאה לפי מה שביקשת
CATEGORIES = [
    "Roblox",
    "Facebook",
    "Nordvpn",
    "Instagram",
    "Kick",
    "Disneyplus",
    "Spotify",
    "Steam",
    "Pandabuy",
    "Amazon",
    "Tlauncher",
    "Callofduty",
    "Github",
    "Snapchat",
    "Cyberghost",
    "Netflix",
    "Reddit",
    "Starplus",
    "Crunchyroll",
    "Nintendo",
    "Epic Games"
]

def load_stock():
    if not os.path.exists(STOCK_FILE):
        initial_data = {cat: [] for cat in CATEGORIES}
        save_stock(initial_data)
        return initial_data
    with open(STOCK_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {cat: [] for cat in CATEGORIES}

def save_stock(data):
    with open(STOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@client.event
async def on_ready():
    await tree.sync()
    print(f"הבוט מחובר בהצלחה בתור {client.user}")

# --- פקודת /STOCK ---
@tree.command(name="stock", description="מציג את כמות המלאי הזמינה מכל קטגוריה")
async def stock(interaction: discord.Interaction):
    stock_data = load_stock()
    
    embed = discord.Embed(
        title="📦 מלאי הבוט הנוכחי",
        color=discord.Color.blue()
    )
    
    description = ""
    for category in CATEGORIES:
        count = len(stock_data.get(category, []))
        description += f"**{category}:** {count} זמינים\n"
        
    embed.description = description
    await interaction.response.send_message(embed=embed, ephemeral=True)

# --- פקודת /ADD_STOCK (למנהלים בלבד) ---
@tree.command(name="add_stock", description="מוסיף חשבון חדש למלאי (למנהלים בלבד)")
@app_commands.choices(category=[
    app_commands.Choice(name=cat, value=cat) for cat in CATEGORIES
])
@app_commands.describe(category="בחר קטגוריה", account="הכנס את פרטי החשבון בפורמט אימייל:סיסמה")
async def add_stock(interaction: discord.Interaction, category: str, account: str):
    role = interaction.guild.get_role(ROLE_MANAGER_ID)
    if not role or role not in interaction.user.roles:
        await interaction.response.send_message("❌ אין לך הרשאה להשתמש בפקודה זו (דרוש רול מנהל).", ephemeral=True)
        return

    stock_data = load_stock()
    if category not in stock_data:
        stock_data[category] = []
        
    stock_data[category].append(account)
    save_stock(stock_data)
    
    await interaction.response.send_message(f"✅ החשבון נוסף בהצלחה לקטגוריה **{category}**!", ephemeral=True)

# --- פקודת /GEN (לבעלי רול FGEN בלבד) ---
@tree.command(name="gen", description="מקבל משתמש אקראי מקטגוריה לבחירתך ישירות לפרטי")
@app_commands.choices(category=[
    app_commands.Choice(name=cat, value=cat) for cat in CATEGORIES
])
@app_commands.describe(category="בחר קטגוריה ממנה תרצה לייצר משתמש")
async def gen(interaction: discord.Interaction, category: str):
    role = interaction.guild.get_role(ROLE_FGEN_ID)
    if not role or role not in interaction.user.roles:
        await interaction.response.send_message("❌ אין לך הרשאה להשתמש בפקודה זו (דרוש רול FGEN).", ephemeral=True)
        return

    stock_data = load_stock()
    accounts = stock_data.get(category, [])
    
    if not accounts:
        await interaction.response.send_message(f"❌ מצטערים, אין כרגע משתמשים זמינים בקטגוריה **{category}**.", ephemeral=True)
        return

    # שליפת המשתמש הראשון ומחיקתו מהרשימה
    account = accounts.pop(0)
    save_stock(stock_data)

    try:
        dm_embed = discord.Embed(
            title=f"🎁 הפרטים שלך עבור {category}",
            description=f"הנה החשבון שקיבלת:\n`{account}`",
            color=discord.Color.green()
        )
        await interaction.user.send(embed=dm_embed)
        await interaction.response.send_message("✅ החשבון נשלח אליך בהצלחה להודעות הפרטיות (DM)!", ephemeral=True)
    except discord.Forbidden:
        # מחזיר את החשבון למלאי אם ההודעות הפרטיות של המשתמש סגורות
        accounts.insert(0, account)
        save_stock(stock_data)
        await interaction.response.send_message("❌ לא הצלחתי לשלוח לך הודעה פרטית. ודא שההודעות הפרטיות שלך פתוחות.", ephemeral=True)

# קריאת הטוקן ממשתני הסביבה ב-Render
TOKEN = os.getenv("DISCORD_TOKEN")
client.run(TOKEN)
