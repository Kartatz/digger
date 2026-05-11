import asyncio
import os
import zipfile
import logging
import time
import json

import hydrogram
import aiofiles
import aiofiles.os
import httpx
import asynczipfile

logging.disable(logging.CRITICAL)

async def main():
	
	async with aiofiles.open(file = "tokens.json", mode = "r") as file:
		text = await file.read()
	
	session_strings = json.loads(s= text)
	
	async with aiofiles.open(file = "channels.json", mode = "r") as file:
		text = await file.read()
	
	channels = json.loads(s= text)
	accounts = []
	account = 0
	
	resume = True
	
	zip = None
	zipname = "document.zip"
	
	resume_chat_id = 0
	resume_message_id = 0
	
	if not os.path.exists("message_id"):
		resume = False
	else:
		async with aiofiles.open(file = "chat_id", mode = "r") as file:
			text = await file.read()
		
		resume_chat_id = int(text)
		
		async with aiofiles.open(file = "message_id", mode = "r") as file:
			text = await file.read()
		
		resume_message_id = int(text)
	
	sum = 0
	
	hclient = httpx.AsyncClient(http2 = True, headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Cromite/147.0.0.0 Chrome/147.0.0.0 Mobile Safari/537.36"})
	
	for (index, session_string) in enumerate(session_strings):
		bot = hydrogram.Client(
			name = str(index),
			api_id = 105810,
			api_hash = "3e7a52498eec003c5896a330e5d29397",
			no_updates = True,
			session_string = session_string,
			message_cache_size = 1
		)
		await bot.start()
		
		accounts.append(bot)
	
	for key, value in channels.items():
		chat_id = int(key)
		message_ids = value
		
		if resume:
			if chat_id != resume_chat_id:
				continue
		
		for message_id in message_ids:
			if resume:
				if message_id != resume_message_id:
					continue
				
				resume = False
				
				continue
			
			bot = accounts[account]
			account += 1
			
			if account >= len(accounts):
				account = 0
			
			message = await bot.get_messages(
				chat_id = chat_id,
				message_ids = message_id
			)
			print(message.document.file_name)
			temporary_file = "/tmp/document.bin"
			
			await message.download(file_name = temporary_file)
			
			stat = await aiofiles.os.stat(path = temporary_file)
			file_size = stat.st_size
			
			assert file_size != 0
			
			sum += file_size
			
			if zip is None:
				zip = await asynczipfile.zipfile_create(
					file = zipname,
					mode = "w",
					compression = zipfile.ZIP_STORED,
					compresslevel = 9
				)
			
			await asynczipfile.zipfile_write(
				instance = zip,
				filename = temporary_file,
				arcname = "%i. %s" % (
					message_id,
					message.document.file_name.replace("/", "_")
				)
			)
			
			await aiofiles.os.remove(path = temporary_file)
			
			maxsize = (1 * 1024 * 1024) - ((1024 * 1024) * 100)
			
			if sum >= maxsize:
				await asynczipfile.zipfile_close(instance = zip)
				
				fp = open(file = zipname, mode = "rb")
				
				files = {
					"file": ("document.zip", fp, "application/octet-stream")
				}
				
				response = await hclient.post(url = "https://store1.filemirage.com/upload.php", files = files)
				print(response.text)
				await aiofiles.os.remove(zipname)
				
				zip = None
				sum = 0
			
			try:
				async with aiofiles.open(file = "chat_id", mode = "w") as file:
					await file.write(str(chat_id))
				
				async with aiofiles.open(file = "message_id", mode = "w") as file:
					await file.write(str(message_id))
			except:
				async with aiofiles.open(file = "chat_id", mode = "w") as file:
					await file.write(str(chat_id))
				
				async with aiofiles.open(file = "message_id", mode = "w") as file:
					await file.write(str(message_id))
				
				raise

asyncio.run(main())
