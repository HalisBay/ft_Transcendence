import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import MatchHistory
from channels.db import database_sync_to_async
User = get_user_model()
# Global oyun durumu ve oda yönetimi
rooms = {}  # {'room_name': {'players': [user1, user2], 'game_state': {...}, 'user_channel_map': {user_id: channel_name}}}
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
                    'players': {},
                    'scores': {},
                },
                'user_channel_map': {}
            }
        room = rooms[self.room_group_name]
        user = self.scope['user']
        self.user = user
        room['players'].append(user)
        room['user_channel_map'][user.id] = self.channel_name
        # Add user to game state
        player_id = f'player{len(room["players"])}'
        room['game_state']['players'][player_id] = {'y': 270.0}
        room['game_state']['scores'][player_id] = 0
        self.player_id = player_id
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
            room['players'].remove(self.user)
            del room['user_channel_map'][self.user.id]
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
            ball['x'] += ball['vx'] * 10
            ball['y'] += ball['vy'] * 10
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
            # Skor 2'ye ulaşan oyuncu kazanır, oyunu bitir
            if game_state['scores']['player1'] == 2:
                await self.end_game("player1")
                break
            elif game_state['scores']['player2'] == 2:
                await self.end_game("player2")
                break
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_state',
                    'state': game_state
                }
            )
            await asyncio.sleep(0.05)
    async def end_game(self, winner):
        global rooms
        room = rooms[self.room_group_name]
        game_state = room['game_state']
        # Determine the winner and loser messages
        players = room['players']
        winner_user = players[0] if winner == "player1" else players[1]
        loser_user = players[0] if winner != "player1" else players[1]
        winner_message = f"You Win! Congrats {winner_user.nick}"
        loser_message = f"You Lose! Try again {loser_user.nick}"
        # Find the channels for the winner and loser
        user_channel_map = room['user_channel_map']
        winner_channel = user_channel_map[winner_user.id]
        loser_channel = user_channel_map[loser_user.id]
        # Send "You Win! Congrats" message to the winner
        await self.channel_layer.send(
            winner_channel,
            {
                'type': 'game_message',
                'message': winner_message
            }
        )
        # Send "You Lose! Try again" message to the loser
        await self.channel_layer.send(
            loser_channel,
            {
                'type': 'game_message',
                'message': loser_message
            }
        )
        # Record match history for both players
        await database_sync_to_async(MatchHistory.objects.create)(
            user=winner_user,
            opponent=loser_user,
            result=True,
            win_count=await database_sync_to_async(lambda: winner_user.match_history.filter(result=True).count() + 1)(),
            lose_count=await database_sync_to_async(lambda: winner_user.match_history.filter(result=False).count())(),
            score=game_state['scores'][winner]
        )
        await database_sync_to_async(MatchHistory.objects.create)(
            user=loser_user,
            opponent=winner_user,
            result=False,
            win_count=await database_sync_to_async(lambda: loser_user.match_history.filter(result=True).count())(),
            lose_count=await database_sync_to_async(lambda: loser_user.match_history.filter(result=False).count() + 1)(),
            score=game_state['scores'][f'player{3 - int(winner[-1])}']
        )
        # Clear players from the room
        del rooms[self.room_group_name]
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