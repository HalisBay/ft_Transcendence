import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

# Global oyun durumu
game_state = {
    'ball': {
        'x': 500.0,
        'y': 290.0,
        'vx': 1.0,
        'vy': 1.0
    },
    'players': {
        'player1': {'y': 270.0},
        'player2': {'y': 270.0}
    },
    'scores': {
        'player1': 0,
        'player2': 0
    }
}

connected_players = 0

class PongConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global connected_players
        self.room_group_name = "pong_game"

        connected_players += 1
        self.player_id = f'player{connected_players}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'message': 'Waiting for another player...'
            }
        )

        if connected_players == 2:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': 'Both players connected. Starting game...'
                }
            )
            await asyncio.sleep(1)  # Small delay before starting the countdown
            asyncio.create_task(self.start_game())

    async def disconnect(self, close_code):
        global connected_players
        connected_players -= 1

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        global game_state
        data = json.loads(text_data)

        if 'move' in data:
            direction = data['move']
            player = game_state['players'][self.player_id]
            if direction == 'up' and player['y'] > 0:
                player['y'] -= 5
            elif direction == 'down' and player['y'] < 520:  # yükseklik - paddle
                player['y'] += 5

    async def start_game(self):
        for countdown in range(4, 0, -1):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_message',
                    'message': f'{countdown}'
                }
            )
            await asyncio.sleep(1)  # Add delay to ensure messages are sent one by one

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
        global game_state
        while connected_players == 2:
            ball = game_state['ball']
            players = game_state['players']

            # Topun pozisyonunu güncelle
            ball['x'] += ball['vx'] * 5
            ball['y'] += ball['vy'] * 5

            # Duvara çarpma kontrolü
            if ball['y'] >= 570 or ball['y'] < 2:
                ball['vy'] = -ball['vy']

            # Çubuğa çarpma kontrolü
            if ball['x'] <= 5 and players['player1']['y'] <= ball['y'] <= players['player1']['y'] + 60:
                ball['vx'] = -ball['vx']
            elif ball['x'] >= 985 and players['player2']['y'] <= ball['y'] <= players['player2']['y'] + 60:
                ball['vx'] = -ball['vx']

            # Top dışarı çıkarsa sayı ve sıfırlama
            if ball['x'] < 0:  # Player 1 kaçırırsa
                game_state['scores']['player2'] += 1
                await self.reset_ball(direction=1)
            elif ball['x'] > 990:  # Player 2 kaçırırsa
                game_state['scores']['player1'] += 1
                await self.reset_ball(direction=-1)

            # Yeni durumu tüm oyunculara gönder
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_state',
                    'state': game_state
                }
            )

            await asyncio.sleep(0.05)

    async def reset_ball(self, direction):
        global game_state
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
