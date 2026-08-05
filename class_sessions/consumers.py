import json
import random
import string
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ClassSession


class QRConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        await self.accept()
        self.keep_running = True
        self.task = asyncio.create_task(self.rotate_code())

    async def disconnect(self, close_code):
        self.keep_running = False

    async def rotate_code(self):
        while self.keep_running:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            await self.save_rotating_code(code)
            await self.send(text_data=json.dumps({
                'code': code
            }))
            await asyncio.sleep(5)

    @database_sync_to_async
    def save_rotating_code(self, code):
        try:
            session = ClassSession.objects.get(id=self.session_id)
            session.rotating_code = code
            session.save()
        except ClassSession.DoesNotExist:
            pass