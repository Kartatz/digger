import asyncio
import os
import zipfile
import logging

import hydrogram
import aiofiles
import aiofiles.os

import asynczipfile

logging.disable(logging.CRITICAL)

async def main():
	
	client = hydrogram.Client(
		name = "user",
		api_id = 105810,
		api_hash = "3e7a52498eec003c5896a330e5d29397",
		no_updates = True,
		session_string = os.getenv("SESSION_STRING")
	)
	
	bot = hydrogram.Client(
		name = "bot",
		api_id = 105810,
		api_hash = "3e7a52498eec003c5896a330e5d29397",
		no_updates = True,
		session_string = os.getenv("BOT_TOKEN")
	)

	await client.start()
	await bot.start()
	
	# print(await client.export_session_string())
	maxsize = (2000 * 1024 * 1024) - ((1024 * 1024) * 50)
	
	offset = 0
	
	async with aiofiles.open(file = "offset", mode = "r") as file:
		text = await file.read()
	
	offset = int(text)
	
	zip = None
	zipname = "document.zip"
	
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
				compression = zipfile.ZIP_LZMA,
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
		
		file_name = (
			file_name
				.replace("_", " ")
				.replace(".epub", "")
				.replace(".pdf", "")
				.replace(".cbz", "")
		)
		
		print("Processing %s (offset = %i)" % (file_name, offset))
		
		old = "document.bin"
		new = message.document.file_name
		
		try:
			await message.download(file_name = old)
		except (hydrogram.errors.FloodPremiumWait, hydrogram.errors.FloodWait) as e:
			await asyncio.sleep(e.value)
			await message.download(file_name = old)
		
		old = ("downloads/" + old)
		
		await asynczipfile.zipfile_write(
			instance = zip,
			filename = old,
			arcname = "%i. %s" % (
				offset,
				new.replace("/", "_")
			)
		)
		
		await asynczipfile.zipfile_close(instance = zip)
		
		await aiofiles.os.remove(path = old)
		
		stat = await aiofiles.os.stat(path = zipname)
		file_size = stat.st_size
		
		if file_size > maxsize:
			chat_id = -1003765641864
			
			await bot.send_document(
				chat_id = chat_id,
				document = zipname
			)
			
			zip = None
			
			async with aiofiles.open(file = "offset", mode = "w") as file:
				text = str(offset)
				await file.write(text)
			
			process = await asyncio.create_subprocess_exec(*("git", "commit", "-m", "Update data", "-a"))
			await process.communicate()
			
			process = await asyncio.create_subprocess_exec(*("git", "push"))
			await process.communicate()
		else:
			zip = await asynczipfile.zipfile_create(
				file = zipname,
				mode = "a",
				compression = zipfile.ZIP_DEFLATED,
				compresslevel = 9
			)
		
		#print(message)
	
	#>await c.stop()

asyncio.run(main())
