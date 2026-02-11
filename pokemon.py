# Pokémon savaş sistemi - DC bot (hepsi tek dosyada)
# Çalıştırmadan: pip install discord.py
# ⬇️ Token'ını BURAYA yaz (Discord Developer Portal → Bot → Reset Token / Copy)
TOKEN = "YOUR_TOKEN_HERE_<3"

import random
import discord
from discord.ext import commands

def rastgele_sayi(a, b):
    return random.randint(a, b)

class Pokemon:
    def __init__(self, pokemon_trainer, name):
        self.pokemon_trainer = pokemon_trainer
        self.name = name
        self.hp = rastgele_sayi(70, 100)
        self.power = rastgele_sayi(10, 20)

    def info(self):
        return f"İsim: {self.name} | HP: {self.hp} | Güç: {self.power}"

    async def attack(self, enemy):
        # Sihirbaz kalkan kontrolü (saldırıya uğrayan düşman sihirbazsa)
        if isinstance(enemy, Wizard):
            if rastgele_sayi(1, 5) == 1:
                return "Sihirbaz Pokémon savaşta bir kalkan kullandı!"
        if enemy.hp > self.power:
            enemy.hp -= self.power
            return f"Pokémon eğitmeni @{self.pokemon_trainer} @{enemy.pokemon_trainer}'ne saldırdı\n@{enemy.pokemon_trainer}'nin sağlık durumu {enemy.hp}"
        enemy.hp = 0
        return f"Pokémon eğitmeni @{self.pokemon_trainer} @{enemy.pokemon_trainer}'ni yendi!"


class Wizard(Pokemon):
    def __init__(self, pokemon_trainer, name):
        super().__init__(pokemon_trainer, name)
        self.hp = rastgele_sayi(85, 120)
        self.power = rastgele_sayi(8, 16)

    def info(self):
        return "Sihirbaz pokémonunuz var.\n" + super().info()

    async def attack(self, enemy):
        return await super().attack(enemy)


class Fighter(Pokemon):
    def __init__(self, pokemon_trainer, name):
        super().__init__(pokemon_trainer, name)
        self.hp = rastgele_sayi(60, 90)
        self.power = rastgele_sayi(15, 28)

    def info(self):
        return "Dövüşçü pokémonunuz var.\n" + super().info()

    async def attack(self, enemy):
        super_guc = rastgele_sayi(5, 15)
        self.power += super_guc
        sonuc = await super().attack(enemy)
        self.power -= super_guc
        return sonuc + f"\nDövüşçü Pokémon süper saldırı kullandı. Eklenen güç: {super_guc}"


# Bonus: sağlık yenileme & kazanma bonusu
def heal(pokemon, miktar=20):
    cap = 120 if isinstance(pokemon, Wizard) else 100
    pokemon.hp = min(pokemon.hp + miktar, cap)

def win_bonus(pokemon):
    heal(pokemon, 15)
    return f"Kazandınız! +15 HP. Güncel HP: {pokemon.hp}"


# --- Discord Bot ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

users_pokemon = {}
battles = {}

@bot.event
async def on_ready():
    print(f"Bot giriş yaptı: {bot.user}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Eksik parametre. Örnek: `!pokemon sihirbaz Pikachu` veya `!pokemon dovuscu Mew`")
        return
    await ctx.send(f"Hata: {error}")

@bot.command()
async def pokemon(ctx, tip: str, *, isim: str):
    """!pokemon sihirbaz Pikachu  veya  !pokemon dovuscu Mew"""
    tip = tip.lower().strip()
    if tip == "sihirbaz":
        users_pokemon[ctx.author.id] = Wizard(str(ctx.author), isim.strip())
    elif tip == "dovuscu":
        users_pokemon[ctx.author.id] = Fighter(str(ctx.author), isim.strip())
    else:
        await ctx.send("Tip: `sihirbaz` veya `dovuscu` yaz.")
        return
    await ctx.send("Pokémon alındı!\n" + users_pokemon[ctx.author.id].info())

@bot.command()
async def bilgi(ctx):
    """Pokémon bilgini gösterir."""
    if ctx.author.id not in users_pokemon:
        await ctx.send("Önce `!pokemon sihirbaz İsim` veya `!pokemon dovuscu İsim` ile Pokémon al.")
        return
    await ctx.send(users_pokemon[ctx.author.id].info())

@bot.command()
async def savas(ctx, rakip: discord.Member):
    """!savas @kullanici - Savaş başlatır."""
    a, b = ctx.author.id, rakip.id
    if a not in users_pokemon or b not in users_pokemon:
        await ctx.send("İkinizin de Pokémon'u olmalı. `!pokemon sihirbaz İsim` kullanın.")
        return
    key = (min(a, b), max(a, b))
    battles[key] = (users_pokemon[a], users_pokemon[b], a)
    await ctx.send(f"Savaş başladı! Sıra @{ctx.author.display_name}'de. `!vur @{rakip.display_name}` ile vur.")

@bot.command()
async def vur(ctx, rakip: discord.Member):
    """Sıra sende ise saldır."""
    a, b = ctx.author.id, rakip.id
    key = (min(a, b), max(a, b))
    if key not in battles:
        await ctx.send("Aktif savaş yok. `!savas @rakip` ile başlat.")
        return
    p1, p2, sira = battles[key]
    if ctx.author.id != sira:
        await ctx.send("Sıra sende değil!")
        return
    saldiran = p1 if sira == a else p2
    dusman = p2 if sira == a else p1
    mesaj = await saldiran.attack(dusman)
    await ctx.send(mesaj)
    if dusman.hp <= 0:
        heal(saldiran, 15)
        del battles[key]
        await ctx.send(f"**Savaş bitti!** Kazanan: {saldiran.pokemon_trainer}. {win_bonus(saldiran)}")
        return
    battles[key] = (p1, p2, b if sira == a else a)
    await ctx.send(f"Sıra @{rakip.display_name}'de. `!vur @{ctx.author.display_name}`")

@bot.command()
async def iyilestir(ctx, miktar: int = 20):
    """HP yenile: !iyilestir  veya !iyilestir 30"""
    if ctx.author.id not in users_pokemon:
        await ctx.send("Önce Pokémon al: `!pokemon sihirbaz İsim`")
        return
    heal(users_pokemon[ctx.author.id], miktar)
    await ctx.send(f"HP yenilendi: {users_pokemon[ctx.author.id].hp}")

if __name__ == "__main__":
    bot.run(TOKEN)