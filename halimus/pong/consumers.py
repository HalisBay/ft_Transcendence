import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

# Global oyun durumu ve oda yönetimi
rooms = {}  # {'room_name': {'players': [player1, player2], 'game_state': {...}}}


class PongConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global rooms

        # Uygun oda bul veya yeni bir oda oluştur
        for room_name, room_data in rooms.items():
            if len(room_data['players']) < 2:
                self.room_group_name = room_name
                break
        else:
            # Yeni oda oluştur
            self.room_group_name = f"pong_game_{len(rooms) + 1}"
            rooms[self.room_group_name] = {
                'players': [],
                'game_state': {
                    'ball': {'x': 500.0, 'y': 290.0, 'vx': 1.0, 'vy': 1.0},
                    'players': {
                        'player1': {'y': 270.0},
                        'player2': {'y': 270.0},
                    },
                    'scores': {'player1': 0, 'player2': 0},
                }
            }

        room = rooms[self.room_group_name]
        player_id = f'player{len(room["players"]) + 1}'
        self.player_id = player_id
        room['players'].append(self.channel_name)

        # Gruba katıl ve bağlantıyı kabul et
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Oyun durumu güncellemesi
        if len(room['players']) == 2:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': 'Both players connected. Starting game...'
                }
            )
            await asyncio.sleep(1)
            asyncio.create_task(self.start_game())

    async def disconnect(self, close_code):
        global rooms

        # Odadan oyuncu çıkar
        room = rooms.get(self.room_group_name, None)
        if room:
            room['players'].remove(self.channel_name)

            # Eğer odada oyuncu kalmadıysa odayı sil
            if not room['players']:
                del rooms[self.room_group_name]
            else:
                # Eğer bir oyuncu kaldıysa oyunu iptal et ve odayı sil
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'game_message',
                        'message': 'A player has disconnected. Game is canceled.'
                    }
                )
                del rooms[self.room_group_name]

        # Gruptan çıkar
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )


    async def receive(self, text_data):
        global rooms
        room = rooms[self.room_group_name]
        game_state = room['game_state']
        data = json.loads(text_data)

        if 'move' in data:
            direction = data['move']
            player = game_state['players'][self.player_id]
            if direction == 'up' and player['y'] > 0:
                player['y'] -= 5
            elif direction == 'down' and player['y'] < 520:  # Paddle height
                player['y'] += 5

    async def start_game(self):
        global rooms
        room = rooms[self.room_group_name]
        game_state = room['game_state']

        for countdown in range(4, 0, -1):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': f'{countdown}'
                }
            )
            await asyncio.sleep(1)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': 'Başla!'
            }
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_state',
                'state': game_state
            }
        )

        asyncio.create_task(self.move_ball())

    async def move_ball(self):
        global rooms
        room = rooms[self.room_group_name]

        if not room:
            return
        
        game_state = room['game_state']

        while len(room['players']) == 2:
            ball = game_state['ball']
            players = game_state['players']

            ball['x'] += ball['vx'] * 5
            ball['y'] += ball['vy'] * 5

            if ball['y'] >= 570 or ball['y'] < 2:
                ball['vy'] = -ball['vy']

            if ball['x'] <= 5 and players['player1']['y'] <= ball['y'] <= players['player1']['y'] + 60:
                ball['vx'] = -ball['vx']
            elif ball['x'] >= 985 and players['player2']['y'] <= ball['y'] <= players['player2']['y'] + 60:
                ball['vx'] = -ball['vx']

            if ball['x'] < 0:
                game_state['scores']['player2'] += 1
                await self.reset_ball(1)
            elif ball['x'] > 990:
                game_state['scores']['player1'] += 1
                await self.reset_ball(-1)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_state',
                    'state': game_state
                }
            )
            await asyncio.sleep(0.05)

    async def reset_ball(self, direction):
        global rooms
        room = rooms[self.room_group_name]
        game_state = room['game_state']
        game_state['ball'] = {
            'x': 500.0,
            'y': 290.0,
            'vx': direction * 1.0,
            'vy': 1.0
        }

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': f'Score: {game_state["scores"]["player1"]} - {game_state["scores"]["player2"]}'
            }
        )

    async def game_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'game_message',
            'message': message
        }))

    async def game_state(self, event):
        state = event['state']
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'state': state
        }))
