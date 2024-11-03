import discord
import yt_dlp as youtube_dl  # Cambiar a yt_dlp
from discord.ext import commands
import tensorflow as tf
from PIL import Image, ImageOps
import numpy as np
import asyncio
import random
import requests
import os


model = tf.keras.models.load_model("./dependencias/keras_model.h5", compile=False)
class_names = open("./dependencias/labels.txt", "r").readlines()
youtube_dl.utils.bug_reports_message = lambda: ''

def get_foxy_image_url():    
    url = 'https://randomfox.ca/floof/'
    res = requests.get(url)
    data = res.json()
    return data['image']

def detect_bird(image_path):
    # Configuración de impresión para evitar notación científica
    np.set_printoptions(suppress=True)

    # Preparar la imagen
    image = Image.open(image_path).convert("RGB")
    size = (224, 224)
    image = ImageOps.fit(image, size, Image.Resampling.LANCZOS)
    
    # Convertir la imagen a una matriz numpy
    image_array = np.asarray(image)
    normalized_image_array = (image_array.astype(np.float32) / 127.5) - 1

    # Crear un array con el tamaño adecuado para el modelo
    data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
    data[0] = normalized_image_array

    # Hacer la predicción
    prediction = model.predict(data)
    index = np.argmax(prediction)
    class_name = class_names[index].strip()  # Limpiar cualquier salto de línea
    confidence_score = prediction[0][index]

    # Crear el mensaje de salida
    result = f"Nombre Ave: {class_name}, Probabilidad: {confidence_score:.2f}"
    if class_name == 'Buhos':
        result += "\nLos búhos representan la sabiduría y la comprensión de la ley."
    elif class_name == 'Lechuzas':
        result += "\nLos lechuzas simbolizan una criatura demoníaca nocturna y un mal presagio."

    return result


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Joins a voice channel"""
        if channel is None and ctx.author.voice:
            channel = ctx.author.voice.channel
        elif channel is None:
            await ctx.send("You need to specify a channel or be in one!")
            return

        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        
        try:
            await channel.connect()
        except Exception as e:
            await ctx.send(f"Failed to join channel: {e}")
            print(f"Failed to join channel: {e}")

    @commands.command()
    async def play(self, ctx, *, query):
        """Plays a file from the local filesystem"""
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(query))
        ctx.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.send(f'Now playing: {query}')

    @commands.command()
    async def yt(self, ctx, *, url):
        """Plays from a url (almost anything yt_dlp supports)"""
        async with ctx.typing():
            print(f"Attempting to play URL: {url}")  # Mensaje de depuración
            player = await YTDLSource.from_url(url, loop=self.bot.loop)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def stream(self, ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.send(f'Now playing: {player.title}')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Changes the player's volume"""
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""
        await ctx.voice_client.disconnect()

    @play.before_invoke
    @yt.before_invoke
    @stream.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.memes = {
            '1.jpg': 5,  
            '2.jpeg': 2,
            '9.jpg': 1, 
            '5.jpg':7,
            '4.jpg':3,
            '3.jpg':4,
            '6.jpg':5,
            '7.jpeg':6,
            '8.jpg':8
        }

    @commands.command()
    async def gen_password(self, ctx):
        contrasena = ""
        caracteres = "+-/*!&$#?=@abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
        for _ in range(8):
            contrasena += random.choice(caracteres)
        await ctx.send(contrasena)

    @commands.command()
    async def gen_emodji(self, ctx):
        emodji = ["\U0001f600", "\U0001f642", "\U0001F606", "\U0001F923", "\U0001F609", "\U0001F60E", "\U0001F605"]
        await ctx.send(random.choice(emodji))

    @commands.command()
    async def flip_coin(self, ctx):
        flip = random.randint(0, 1)
        if flip == 0:
            await ctx.send("CARA")
        else:
            await ctx.send("SELLO")

    @commands.command()
    async def hello(self, ctx):
        await ctx.send(f'Hola, soy un bot multifuncional {self.bot.user}!')

    @commands.command()
    async def heh(self, ctx, count_heh=5):
        await ctx.send("he" * count_heh)

    @commands.command()
    async def meme(self, ctx):
        meme_files = list(self.memes.keys())
        meme_weights = list(self.memes.values())
        selected_meme = random.choices(meme_files, weights=meme_weights, k=1)[0]
        meme_path = os.path.join('C:/Users/Asus/Documents/kodlan/proyect_Python/BOT/img', selected_meme)

        with open(meme_path, 'rb') as f:
            picture = discord.File(f)
        await ctx.send(file=picture)
    
    @commands.command()
    async def foxy(self, ctx):
        picture = get_foxy_image_url()
        await ctx.send(picture)
        
    @commands.command()
    async def detectar_ave(self, ctx):
        if len(ctx.message.attachments) == 0:
            await ctx.send("Por favor, sube una imagen.")
            return

        # Descarga la imagen adjunta
        attachment = ctx.message.attachments[0]
        image_path = f"./{attachment.filename}"
        await attachment.save(image_path)

        # Llama a la función de detección de aves
        result = detect_bird(image_path)

        # Enviar el resultado al canal
        await ctx.send(result)
        # Elimina la imagen local para no llenar el almacenamiento
        os.remove(image_path)


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', intents=intents)

@bot.event
async def on_ready():
    print(f'Hemos iniciado sesión como {bot.user}')

async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.add_cog(Fun(bot))
        await bot.start("token")

asyncio.run(main())
