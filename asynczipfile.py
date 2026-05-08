import asyncio
import functools

import zipfile

async def zipfile_create(**kwargs):
	
	loop = asyncio.get_running_loop()
	
	func = functools.partial(
		zipfile.ZipFile,
		**kwargs
	)
	
	instance = await loop.run_in_executor(None, func)
	
	return instance

async def zipfile_write(instance, **kwargs):
	
	loop = asyncio.get_running_loop()
	
	func = functools.partial(
		instance.write,
		**kwargs
	)
	
	instance = await loop.run_in_executor(None, func)
	
	return instance

async def zipfile_extractall(instance, **kwargs):
	
	loop = asyncio.get_running_loop()
	
	func = functools.partial(
		instance.extractall,
		**kwargs
	)
	
	instance = await loop.run_in_executor(None, func)
	
	return instance

async def zipfile_close(instance):
	
	loop = asyncio.get_running_loop()
	
	func = functools.partial(
		instance.close
	)
	
	await loop.run_in_executor(None, func)
	
	return None


