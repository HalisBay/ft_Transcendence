import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import MatchHistory, Tournament, TournamentParticipant
from channels.db import database_sync_to_async
import string,random

User = get_user_model()
# Global oyun durumu ve oda yönetimi
rooms = (
    {}
)  # {'room_name': {'players': [user1, user2], 'game_state': {...}, 'user_channel_map': {user_id: channel_name}}}

class PongConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global rooms
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        # Eğer oyuncu daha önce bir odadaysa, onu o odadan çıkar ve (zorunlu ise) bağlantısını kapat.
        for room_name, room_data in list(rooms.items()):
            if self.user in room_data["players"]:
                # Bu oyuncunun eski odadan ayrılması için force disconnect mesajı gönderelim
                await self.leave_room(room_name)
                break

        # Uygun oda bul veya yeni bir oda oluştur
        for room_name, room_data in rooms.items():
            if len(room_data["players"]) < 2:
                self.room_group_name = room_name
                print(f"✔️ Mevcut oda bulundu: {self.room_group_name}")
                break
        else:
            # Yeni oda oluştur
            def generate_room_name():
                return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

            self.room_group_name = f"pong_game_{generate_room_name()}"
            rooms[self.room_group_name] = {
                "players": [],
                "game_state": {
                    "ball": {"x": 500.0, "y": 290.0, "vx": 1.0, "vy": 1.0},
                    "players": {},
                    "scores": {},
                },
                "user_channel_map": {},
            }
            print(f"🆕 Yeni oda oluşturuldu: {self.room_group_name}")

        room = rooms[self.room_group_name]
        print(f"📋 Oda durumu: {room}")

        # Aynı kullanıcının kendisiyle oynamasını engelle (örn. aynı odada iki kez olmaması)
        if len(room["players"]) == 1 and room["players"][0] == self.user:
            await self.close()
            return

        room["players"].append(self.user)
        room["user_channel_map"][self.user.id] = self.channel_name

        # Oyuncuya bir player ID ata
        player_id = f'player{len(room["players"])}'
        room["game_state"]["players"][player_id] = {"y": 270.0}
        room["game_state"]["scores"][player_id] = 0
        self.player_id = player_id

        # Gruba katıl ve bağlantıyı kabul et
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        
        print(f"✅ Kullanıcı {self.user} odaya eklendi. Oda oyuncu durumu: {room['players']}")
        
        # Eğer oda doluysa oyunu başlat
        if len(room["players"]) == 2:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_message",
                    "message": "Both players connected. Starting game...",
                },
            )
            await asyncio.sleep(1)
            asyncio.create_task(self.start_game())


    async def leave_room(self, room_name):
        global rooms
        if room_name in rooms:
            room = rooms[room_name]
            if self.user in room["players"]:
                room["players"].remove(self.user)
                room["user_channel_map"].pop(self.user.id, None)
            # Eğer oda boşsa tamamen kaldır
            if not room["players"]:
                del rooms[room_name]
            else:
                # Eğer odada hâlâ oyuncu varsa, "force disconnect" mesajı göndererek
                # diğer oyuncunun da bağlantısını kapatmasını sağlayabilirsiniz.
                await self.channel_layer.group_send(
                    room_name,
                    {"type": "force_disconnect"}
            )

    async def force_disconnect(self, event):
        # Bu mesajı alan oyuncu, bağlantısını kapatır.
        await self.close()



    async def disconnect(self, close_code):
        global rooms
        room = rooms.get(self.room_group_name, None)

        if room:
            # First, remove the user from the room
            if self.user in room["players"]:
                room["players"].remove(self.user)
                del room["user_channel_map"][self.user.id]
            
            # If there are no players left, delete the room entirely
            if not room["players"]:
                del rooms[self.room_group_name]
            else:
                # If there is still a player left, consider them the winner
                remaining_player = room["players"][0]
                
                # Log the match result (no actual game played, score is 0)
                await database_sync_to_async(MatchHistory.objects.create)(
                    user=remaining_player,
                    opponent=self.user,
                    result=True,
                    win_count=await database_sync_to_async(
                        lambda: remaining_player.match_history.filter(result=True).count() + 1
                    )(),
                    lose_count=await database_sync_to_async(
                        lambda: remaining_player.match_history.filter(result=False).count()
                    )(),
                    score=0,  # No game played, so score is 0
                    tWinner=False,
                )
                await database_sync_to_async(MatchHistory.objects.create)(
                    user=self.user,
                    opponent=remaining_player,
                    result=False,
                    win_count=await database_sync_to_async(
                        lambda: self.user.match_history.filter(result=True).count()
                    )(),
                    lose_count=await database_sync_to_async(
                        lambda: self.user.match_history.filter(result=False).count() + 1
                    )(),
                    score=0,  # No game played, so score is 0
                    tWinner=False,
                )
                
                # Notify that a player disconnected and the game is canceled
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "game_message",
                        "message": "A player has disconnected. Game is canceled.",
                    },
                )
                
                # Enable "Next Game" button for the next round
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "enable_next_game_button"}
                )
            
            # Finally, make sure to remove the player from the room and discard the group
            del rooms[self.room_group_name]
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)






    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        global rooms
        room = rooms[self.room_group_name]
        game_state = room["game_state"]
        data = json.loads(text_data)
        if "move" in data:
            direction = data["move"]
            player = game_state["players"][self.player_id]
            if direction == "up" and player["y"] > 0:
                player["y"] -= 5
            elif direction == "down" and player["y"] < 520:  # Paddle height
                player["y"] += 5


    async def start_game(self):
        global rooms
        print(f"📝 Oda adı start_game: {self.room_group_name}")
        if self.room_group_name not in rooms:
            print(f"⚠️ Hata: {self.room_group_name} odası bulunamadı, oyun başlatılamıyor.")
            return  # Eğer oda silinmişse oyunu başlatma


    # Oyun başlatma mantığını burada devam ettir
        print(f"✅ {self.room_group_name} için oyun başlatılıyor.")
        try:
            room = rooms[self.room_group_name]
        except KeyError:
            print(f"⚠️ Hata: {self.room_group_name} odası bulunamadı, oyun başlatılamıyor.")
            return

        print(f"✅ Oda durumu: {room}")
        game_state = room["game_state"]
        for countdown in range(4, 0, -1):
           if not len(room["players"]) < 2:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "game_message", "message": f"{countdown}"},
                )
                await asyncio.sleep(1)
        if not len(room["players"]) < 2:
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "game_message", "message": "Başla!"}
            )
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "game_state", "state": game_state}
        )
        asyncio.create_task(self.move_ball())

    async def move_ball(self):
        global rooms
        room = rooms[self.room_group_name]
        if not room:
            return
        game_state = room["game_state"]
        while len(room["players"]) == 2:
            ball = game_state["ball"]
            players = game_state["players"]
            ball["x"] += ball["vx"] * 10
            ball["y"] += ball["vy"] * 10
            if ball["y"] >= 570 or ball["y"] < 2:
                ball["vy"] = -ball["vy"]
            if (
                ball["x"] <= 5
                and players["player1"]["y"] <= ball["y"] <= players["player1"]["y"] + 60
            ):
                ball["vx"] = -ball["vx"]
            elif (
                ball["x"] >= 985
                and players["player2"]["y"] <= ball["y"] <= players["player2"]["y"] + 60
            ):
                ball["vx"] = -ball["vx"]
            if ball["x"] < 0:
                game_state["scores"]["player2"] += 1
                await self.reset_ball(1)
            elif ball["x"] > 990:
                game_state["scores"]["player1"] += 1
                await self.reset_ball(-1)
            # Skor 2'ye ulaşan oyuncu kazanır, oyunu bitir
            if game_state["scores"]["player1"] == 2:
                await self.end_game("player1")
                break
            elif game_state["scores"]["player2"] == 2:
                await self.end_game("player2")
                break
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "game_state", "state": game_state}
            )
            await asyncio.sleep(0.05)

    async def end_game(self, winner):
        global rooms
        room = rooms[self.room_group_name]
        game_state = room["game_state"]
        # Determine the winner and loser messages
        players = room["players"]
        winner_user = players[0] if winner == "player1" else players[1]
        loser_user = players[0] if winner != "player1" else players[1]
        winner_message = f"You Win! Congrats {winner_user.nick}. Click 'Next Game' to start a new game."
        loser_message = f"You Lose! Try again {loser_user.nick}. Click 'Next Game' to start a new game."
        # Find the channels for the winner and loser
        user_channel_map = room["user_channel_map"]
        winner_channel = user_channel_map[winner_user.id]
        loser_channel = user_channel_map[loser_user.id]
        # Send "You Win! Congrats" message to the winner
        await self.channel_layer.send(
            winner_channel, {"type": "game_message", "message": winner_message}
        )
        # Send "You Lose! Try again" message to the loser
        await self.channel_layer.send(
            loser_channel, {"type": "game_message", "message": loser_message}
        )

        # Enable the 'Next Game' button
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "enable_next_game_button",
            }
    )
        # Record match history for both players
        await database_sync_to_async(MatchHistory.objects.create)(
            user=winner_user,
            opponent=loser_user,
            result=True,
            win_count=await database_sync_to_async(
                lambda: winner_user.match_history.filter(result=True).count() + 1
            )(),
            lose_count=await database_sync_to_async(
                lambda: winner_user.match_history.filter(result=False).count()
            )(),
            score=game_state["scores"][winner],
            tWinner=False,
        )
        await database_sync_to_async(MatchHistory.objects.create)(
            user=loser_user,
            opponent=winner_user,
            result=False,
            win_count=await database_sync_to_async(
                lambda: loser_user.match_history.filter(result=True).count()
            )(),
            lose_count=await database_sync_to_async(
                lambda: loser_user.match_history.filter(result=False).count() + 1
            )(),
            score=game_state["scores"][f"player{3 - int(winner[-1])}"],
            tWinner=False,
        )
        # Clear players from the room
        del rooms[self.room_group_name]


        # Consumer.py
    async def enable_next_game_button(self, event):
        # Frontend'e "Next Game" butonunun etkinleştirildiği bilgisini gönderiyoruz
        await self.send(text_data=json.dumps({
            "type": "enable_next_game_button",  # Bu tip, frontend tarafından işlenecek
        }))



    async def reset_ball(self, direction):
        global rooms
        room = rooms[self.room_group_name]
        game_state = room["game_state"]
        game_state["ball"] = {"x": 500.0, "y": 290.0, "vx": direction * 1.0, "vy": 1.0}
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "game_message",
                "message": f'Score: {game_state["scores"]["player1"]} - {game_state["scores"]["player2"]}',
            },
        )

    async def game_message(self, event):
        message = event["message"]
        await self.send(
            text_data=json.dumps({"type": "game_message", "message": message})
        )

    async def game_state(self, event):
        state = event["state"]
        await self.send(text_data=json.dumps({"type": "game_state", "state": state}))


from channels.db import database_sync_to_async
from .models import Tournament, TournamentParticipant, User
import json


class TournamentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "tournament_group"
        self.user = self.scope["user"]

        # Kullanıcı doğrulaması
        if not self.user.is_authenticated:
            await self.close()  # Bağlantıyı kapat
            return

        await self.accept()  # WebSocket bağlantısını kabul et

        # Grupta bu kanal adı ile katılım sağla
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        # Başlangıç mesajı gönderme
        try:
            await self.send(
                text_data=json.dumps({"message": "Connected to tournament room"})
            )
        except Exception as e:
            print(f"Error while sending initial message: {e}")

    async def disconnect(self, close_code):
        # Kanalı gruptan çı
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        print(f"Disconnected: {self.channel_name}, code: {close_code}")

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action", None)

        if action == "create_tournament":
            creator_alias = data.get("creator_alias")
            tournament_name = data.get("tournament_name")

            if await self.is_user_in_any_tournament():
                await self.send(
                    text_data=json.dumps(
                        {
                            "message": "You are already a participant in another tournament. You cannot create a new tournament."
                        }
                    )
                )
                await self.close()
                return

            tournament = await self.create_tournament(creator_alias, tournament_name)
            if not tournament:
                return
            if isinstance(tournament, str):  # Hata mesajı dönüyorsa
                if self.channel_name:
                    await self.send(
                        text_data=json.dumps(
                            {"message": tournament}  # Bu, hata mesajını döndürecek
                        )
                    )
                await self.close()
            elif tournament:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message": f"Tournament '{tournament_name}' created by {creator_alias}"
                        }
                    )
                )
            else:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message": "An unknown error occurred while creating the tournament."
                        }
                    )
                )

        elif action == "join_tournament":
            player_alias = data.get("player_alias")
            tournament_name = data.get("tournament_name")

            if await self.is_user_in_any_tournament():
                await self.send(
                    text_data=json.dumps(
                        {
                            "message": "You are already a participant in another tournament. You cannot join a new tournament."
                        }
                    )
                )
                await self.close()
                return

            tournament = await self.get_tournament_by_name(tournament_name)
            if tournament:
                # Oturum açmış kullanıcıyla katılım işlemi
                participant = await self.add_player_to_tournament(
                    tournament, player_alias
                )

                if participant:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "message": f"User with alias '{player_alias}' joined the tournament '{tournament_name}'."
                            }
                        )
                    )
                else:
                    await self.send(
                        text_data=json.dumps(
                            {
                                "message": f"Could not add player to the tournament '{tournament_name}'."
                            }
                        )
                    )
                    await self.close()
            else:
                await self.send(
                    text_data=json.dumps(
                        {"message": f"Tournament '{tournament_name}' not found."}
                    )
                )
                await self.close()

    async def create_tournament(self, creator_alias, tournament_name):
        if await database_sync_to_async(
            Tournament.objects.filter(tournament_name=tournament_name).exists
        )():
            await self.send(
                text_data=json.dumps(
                    {"error": "Tournament with this name already exists"}
                )
            )
            await self.close(code=4000)  # Bağlantıyı kapat
            return None

        try:
            # Create the tournament
            tournament = await database_sync_to_async(Tournament.objects.create)(
                creator_alias=creator_alias, tournament_name=tournament_name
            )

            # Add the creator as a participant
            await database_sync_to_async(TournamentParticipant.objects.create)(
                user=self.user, tournament=tournament, alias=creator_alias
            )

            # Send success message if the connection is still open
            if self.channel_name:
                await self.send(
                    text_data=json.dumps(
                        {
                            "message": f"Tournament {tournament_name} created successfully."
                        }
                    )
                )

            return tournament

        except Exception as e:
            print(f"Error while creating tournament: {e}")
            # Send error message if the connection is still open
            if self.channel_name:
                await self.send(
                    text_data=json.dumps(
                        {"error": "An error occurred while creating the tournament"}
                    )
                )
            await self.close()  # Close the WebSocket connection
            return None

    @database_sync_to_async
    def get_tournament_by_name(self, tournament_name):
        return Tournament.objects.filter(tournament_name=tournament_name).first()

    @database_sync_to_async
    def add_player_to_tournament(self, tournament, player_alias):
        try:
            # Turnuvada bu alias'a sahip bir katılımcı var mı diye kontrol et
            existing_participant = TournamentParticipant.objects.filter(
                alias=player_alias, tournament=tournament
            ).first()

            if existing_participant:
                # Eğer alias zaten varsa, hata mesajı gönder
                return None

            existing_user_participant = TournamentParticipant.objects.filter(
                user=self.user, tournament=tournament
            ).first()

            if existing_user_participant:
                return None

            # Katılımcı kullanıcıyı oturum açmış kullanıcıyla eşleştir
            participant = TournamentParticipant.objects.create(
                user=self.user,  # Burada oturum açmış kullanıcıyı alıyoruz
                tournament=tournament,
                alias=player_alias,
            )

            return participant  # Katılım başarıyla oluşturuldu

        except Exception as e:
            print(f"Error while adding player to tournament: {e}")
            return None

    @database_sync_to_async
    def get_participant_by_alias(self, player_alias, tournament):
        # Turnuvada bu alias'a sahip bir katılımcı var mı diye kontrol et
        return TournamentParticipant.objects.filter(
            alias=player_alias, tournament=tournament
        ).first()

    @database_sync_to_async
    def is_user_in_any_tournament(self):
        # Kullanıcının başka bir turnuvaya katılıp katılmadığını kontrol et
        return TournamentParticipant.objects.filter(user=self.user).exists()
