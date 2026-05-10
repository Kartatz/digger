import asyncio
import os
import zipfile
import logging
import time
import json

import hydrogram
import aiofiles
import aiofiles.os

import asynczipfile

logging.disable(logging.CRITICAL)

async def handler(client, message):
	await message.copy(chat_id = -1002110344067)

def human(size):
	for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
		if size < 1024 or unit == "PB":
			return f"{size:.2f} {unit}"
		size /= 1024

async def upload(client, document, offset):
	
	await client.send_document(
		chat_id = -1003765641864,
		document = document,
		file_name = "document.zip"
	)
	
	await aiofiles.os.remove(path = document)

async def main():
	
	print("Start %i" % (0))
	
	client = hydrogram.Client(
		name = "user",
		api_id = 105810,
		api_hash = "3e7a52498eec003c5896a330e5d29397",
		no_updates = True,
		takeout = True,
		session_string = os.getenv("SESSION_STRING")
	)
	
	await client.start()
	
	async with aiofiles.open(file = "tokens.json", mode = "r") as file:
		text = await file.read()
	
	session_strings = json.loads(s= text)
	
	accounts = []
	
	for (index, session_string) in enumerate(session_strings):
		bot = hydrogram.Client(
			name = str(index),
			api_id = 105810,
			api_hash = "3e7a52498eec003c5896a330e5d29397",
			no_updates = False,
			session_string = session_string
		)
		await bot.start()
		
		bot.add_handler(hydrogram.handlers.MessageHandler(handler, hydrogram.filters.private & hydrogram.filters.document))
		
		print("Start %i" % (index))
		
		me = await bot.get_me()
		bot.me = me
		
		await client.promote_chat_member(
			chat_id = -1003765641864,
			user_id = me.username,
			privileges = hydrogram.types.ChatPrivileges(
				can_post_messages=True,
			)
		)
		
		await client.promote_chat_member(
			chat_id = -1002110344067,
			user_id = me.username,
			privileges = hydrogram.types.ChatPrivileges(
				can_post_messages=True,
			)
		)
		
		accounts.append(bot)
	
	me = await client.get_me()
	
	account = 0
	_account = 0
	
	# print(await client.export_session_string())
	maxsize = (2000 * 1024 * 1024) - ((1024 * 1024) * 100)
	
	offset = 0
	file_size = 0
	sum = 0
	
	async with aiofiles.open(file = "offset", mode = "r") as file:
		text = await file.read()
	
	offset = int(text)
	
	zip = None
	zipname = "document.zip"
	
	task = None
	tasks = []
	
	count = 0
	
	async for message in client.search_messages(
		-1002315132889,
		query = "",
		offset = offset,
		filter = hydrogram.enums.MessagesFilter.DOCUMENT
	):
		
		if zip is None:
			zip = await asynczipfile.zipfile_create(
				file = zipname,
				mode = "w",
				compression = zipfile.ZIP_STORED,
				compresslevel = 9
			)
		
		offset += 1
		
		if not message.document:
			continue
		
		file_name = message.document.file_name
		
		if not file_name.endswith((".epub", ".pdf", ".cbz")):
			continue
		
		if file_name.endswith((".pdf")) and message.document.file_size > ((1024 * 1024) * 50):
			continue
		
		if message.document.file_size >= ((1024 * 1024) * 100):
			continue
		
		file_name = (
			file_name
				.replace("_", " ")
				.replace(".epub", "")
				.replace(".pdf", "")
				.replace(".cbz", "")
		)
		
		print("Processing %s (offset = %i, size = '%s')" % (file_name, offset, human(sum)))
		
		old = "document.bin"
		new = message.document.file_name
		
		"""
		message = await message.copy(chat_id = -1002098959553)
		
		submessage = message
		
		bot = accounts[account]
		
		account += 1
		
		if account >= len(accounts):
			account = 0
		
		message = await bot.get_messages(
			chat_id = message.chat.id,
			message_ids = message.id
		)
		"""
		
		try:
			await message.download(file_name = old)
		except (hydrogram.errors.FloodPremiumWait, hydrogram.errors.FloodWait) as e:
			await asyncio.sleep(e.value)
			await message.download(file_name = old)
		
		# await submessage.delete()
		
		stat = await aiofiles.os.stat(path = ("downloads/" + old))
		file_size = stat.st_size
			
		assert file_size != 0
		
		old = ("downloads/" + old)
		
		await asynczipfile.zipfile_write(
			instance = zip,
			filename = old,
			arcname = "%i. %s" % (
				offset,
				new.replace("/", "_")
			)
		)
		
		await aiofiles.os.remove(path = old)
		
		sum += file_size
		
		if sum > maxsize:
			await asynczipfile.zipfile_close(instance = zip)
			
			old = zipname
			new = f"document-{int(time.time())}.zip"
			
			await aiofiles.os.rename(old, new)
			
			print("Start upload")
			
			bot = accounts[_account]
			
			task = asyncio.create_task(
				coro = upload(client = bot, document = new, offset = offset)
			)
			
			tasks.append(task)
			
			if len(tasks) == len(accounts):
				await asyncio.gather(*tasks)
				
				async with aiofiles.open(file = "offset", mode = "w") as file:
					text = str(offset)
					await file.write(text)
				
				process = await asyncio.create_subprocess_exec(*("git", "commit", "-m", "Update data", "-a"))
				await process.communicate()
				
				process = await asyncio.create_subprocess_exec(*("git", "push"))
				await process.communicate()
				
				tasks.clear()
			
			zip = None
			
			_account += 1
			
			if _account >= len(accounts):
				_account = 0
			
			sum = 0
		
		

asyncio.run(main())
