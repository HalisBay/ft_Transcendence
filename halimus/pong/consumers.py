import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from .models import MatchHistory, Tournament, TournamentParticipant
from channels.db import database_sync_to_async
import string,random
from urllib.parse import parse_qs

User = get_user_model()
tournament_win_counts = {}
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

        # URL query params içinden mod ve alias bilgisini al
        query_params = parse_qs(self.scope["query_string"].decode())
        is_tournament_mode = query_params.get("tournament_mode", ["false"])[0] == "true"
        alias = query_params.get("alias", [None])[0] 

        # Eğer oyuncu zaten bir odadaysa, eski odadan çıkar
        for room_name, room_data in list(rooms.items()):
            if self.user in room_data["players"]:
                await self.leave_room(room_name)
                break

        self.room_group_name = "default"
        
        def generate_room_name():
            return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        if is_tournament_mode:
            # Mevcut bir turnuva odası var mı kontrol et
            tournament_room = None
            for room_name, room_data in rooms.items():
                if room_name.startswith("tournament_") and len(room_data["players"]) < 2:
                    tournament_room = room_name
                    break

            if tournament_room:
                self.room_group_name = tournament_room
                print(f"✔️ Mevcut turnuva odasına bağlanılıyor: {self.room_group_name}")
            else:
                # Yeni turnuva odası oluştur
                def generate_room_name():
                    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                self.room_group_name = f"tournament_{generate_room_name()}"  # ✅ Rastgele oda ismi ata
                
                rooms[self.room_group_name] = {
                    "players": [],
                    "game_state": {
                        "ball": {"x": 500.0, "y": 290.0, "vx": 1.0, "vy": 1.0},
                        "players": {},
                        "scores": {},
                    },
                    "user_channel_map": {},
                }
                print(f"🆕 Yeni turnuva odası oluşturuldu: {self.room_group_name}")
            # else:
            #     print(f"✔️ Mevcut turnuva odasına bağlanılıyor: {self.room_group_name}")

        else:
            # 1v1 Modu: Boş bir oda varsa ona katıl, yoksa yeni bir oda oluştur
            for room_name, room_data in rooms.items():
                if room_name.startswith("pong_1v1") and len(room_data["players"]) < 2:
                    self.room_group_name = room_name
                    print(f"✔️ Mevcut 1v1 odasına katılıyor: {self.room_group_name}")
                    break
            else:
                # Yeni 1v1 odası oluştur
                def generate_room_name():
                    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                self.room_group_name = f"pong_1v1_{generate_room_name()}"
                rooms[self.room_group_name] = {
                    "players": [],
                    "game_state": {
                        "ball": {"x": 500.0, "y": 290.0, "vx": 1.0, "vy": 1.0},
                        "players": {},
                        "scores": {},
                    },
                    "user_channel_map": {},
                }
                print(f"🆕 Yeni 1v1 odası oluşturuldu: {self.room_group_name}")

        room = rooms[self.room_group_name]
        print(f"📋 Oda durumu: {room}")

        # Aynı kullanıcının kendisiyle eşleşmesini engelle
        if len(room["players"]) == 1 and room["players"][0] == self.user:
            await self.close()
            return

        # Kullanıcıyı odaya ekle
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
            # Kullanıcıyı odadan çıkar
            if self.user in room["players"]:
                room["players"].remove(self.user)
                del room["user_channel_map"][self.user.id]

            is_tournament = self.room_group_name.startswith("tournament_")

            # Eğer turnuva oyuncusuysa, win count'u temizle
            if is_tournament and self.user.id in tournament_win_counts:
                del tournament_win_counts[self.user.id]

            # Eğer odada kimse kalmadıysa, tamamen sil
            if not room["players"]:
                del rooms[self.room_group_name]
            else:
                # Odada kalan oyuncu varsa, hükmen galip ilan et
                remaining_player = room["players"][0]

                if is_tournament:
                    if remaining_player.id not in tournament_win_counts:
                        tournament_win_counts[remaining_player.id] = 0
                    tournament_win_counts[remaining_player.id] += 1  # Hükmen galibiyet

                is_tournament_winner = is_tournament and tournament_win_counts[remaining_player.id] == 3

                # Genel win_count güncelle
                win_count = await database_sync_to_async(
                    lambda: remaining_player.match_history.filter(result=True).count() + 1
                )()

                # Turnuva win count kontrolü
                tournament_wins = tournament_win_counts[remaining_player.id] if is_tournament else None

                # Maç geçmişini kaydet (hükmen kazanan)
                await database_sync_to_async(MatchHistory.objects.create)(
                    user=remaining_player,
                    opponent=self.user,
                    result=True,
                    win_count=win_count,
                    lose_count=await database_sync_to_async(
                        lambda: remaining_player.match_history.filter(result=False).count()
                    )(),
                    score=11,  # Hükmen galibiyet
                    opponent_score=0,
                    tWinner=is_tournament_winner,
                    is_tournament=is_tournament,
                )

                # Maç geçmişini kaydet (hükmen kaybeden)
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
                    score=0,
                    opponent_score=11,
                    tWinner=False,
                    is_tournament=is_tournament,
                )

                # Kullanıcıya mesaj gönder
                winner_message = f"You Win! Congrats {remaining_player.nick}. Click 'Next Game' to start a new game."
                if is_tournament_winner:
                    winner_message += " 🎉 You are the TOURNAMENT CHAMPION! 🏆"

                user_channel_map = room["user_channel_map"]
                winner_channel = user_channel_map[remaining_player.id]

                await self.channel_layer.send(
                    winner_channel, {"type": "game_message", "message": winner_message}
                )

                # Eğer turnuva kazananı belirlendiyse, temizle
                if is_tournament_winner:
                    del tournament_win_counts[remaining_player.id]

                # 'Next Game' butonunu etkinleştir
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {"type": "enable_next_game_button"}
                )

                # Odayı temizle
                if self.room_group_name in rooms:
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
                print(f"Player 2 scored. New score: {game_state['scores']['player2']}")
                await self.reset_ball(1)
            elif ball["x"] > 990:
                game_state["scores"]["player1"] += 1
                print(f"Player 1 scored. New score: {game_state['scores']['player1']}")
                await self.reset_ball(-1)
            # Skor 2'ye ulaşan oyuncu kazanır, oyunu bitir
            if game_state["scores"]["player1"] == 2:
                await self.end_game("player1")
                print("Player 1 won the game.")
                break
            elif game_state["scores"]["player2"] == 2:
                await self.end_game("player2")
                print("Player 2 won the game.")
                break
            await self.channel_layer.group_send(
                self.room_group_name, {"type": "game_state", "state": game_state}
            )
            await asyncio.sleep(0.05)

    async def end_game(self, winner):
        global rooms
        room = rooms[self.room_group_name]
        game_state = room["game_state"]

        # Kazanan ve kaybedeni belirle
        players = room["players"]
        winner_user = players[0] if winner == "player1" else players[1]
        loser_user = players[0] if winner != "player1" else players[1]

        # Eğer maç bir turnuva maçına aitse turnuva kazançlarını güncelle
        is_tournament = self.room_group_name.startswith("tournament_")
        if is_tournament:
            if winner_user.id not in tournament_win_counts:
                tournament_win_counts[winner_user.id] = 0
            tournament_win_counts[winner_user.id] += 1

            if loser_user.id in tournament_win_counts:
                del tournament_win_counts[loser_user.id]

        # Turnuva galibi mi?
        is_tournament_winner = is_tournament and tournament_win_counts[winner_user.id] == 3  # 3 galibiyet şampiyonluk

        # Mesajları belirle
        winner_message = f"You Win! Congrats {winner_user.nick}. Click 'Next Game' to start a new game."
        if is_tournament_winner:
            winner_message += " 🎉 You are the TOURNAMENT CHAMPION! 🏆"

        loser_message = f"You Lose! Try again {loser_user.nick}. Click 'Next Game' to start a new game."

        # Mesajları ilgili kullanıcılara gönder
        user_channel_map = room["user_channel_map"]
        winner_channel = user_channel_map[winner_user.id]
        loser_channel = user_channel_map[loser_user.id]

        await self.channel_layer.send(
            winner_channel, {"type": "game_message", "message": winner_message}
        )
        await self.channel_layer.send(
            loser_channel, {"type": "game_message", "message": loser_message}
        )

        # 'Next Game' butonunu etkinleştir
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "enable_next_game_button"}
        )

        # Genel kazanma sayısı (hem 1v1 hem turnuva)
        win_count = await database_sync_to_async(
            lambda: winner_user.match_history.filter(result=True).count() + 1
        )()

        # Eğer turnuva maçıysa, turnuva kazançlarını kaydet
        tournament_wins = tournament_win_counts[winner_user.id] if is_tournament else None

        # Maç geçmişini kaydet (kazanan)
        await database_sync_to_async(MatchHistory.objects.create)(
            user=winner_user,
            opponent=loser_user,
            result=True,
            win_count=win_count,
            lose_count=await database_sync_to_async(
                lambda: winner_user.match_history.filter(result=False).count()
            )(),
            score=game_state["scores"][winner],
            opponent_score=game_state["scores"][f"player{3 - int(winner[-1])}"],
            tWinner=is_tournament_winner,
            is_tournament=is_tournament,
        )

        # Maç geçmişini kaydet (kaybeden)
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
            opponent_score=game_state["scores"][winner],
            tWinner=False,
            is_tournament=is_tournament,
        )

        # Turnuva kazananı belirlendiyse listeden temizle
        if is_tournament_winner:
            del tournament_win_counts[winner_user.id]

        # Oda temizleme
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


# from channels.db import database_sync_to_async
# from .models import Tournament, TournamentParticipant, User
# import json


# class TournamentConsumer(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.room_group_name = "tournament_group" #TODO: değişebilir 
#         self.user = self.scope["user"]

#         # Kullanıcı doğrulaması
#         if not self.user.is_authenticated:
#             await self.close()  # Bağlantıyı kapat
#             return

#         await self.accept()  # WebSocket bağlantısını kabul et

#         # Grupta bu kanal adı ile katılım sağla
#         await self.channel_layer.group_add(self.room_group_name, self.channel_name)

#         try:
#             await self.send(
#                 text_data=json.dumps({"message": "Connected to tournament room"})
#             )
#         except Exception as e:
#             print(f"Error while sending initial message: {e}")

#     async def disconnect(self, close_code):
#         tournament = await self.get_user_tournament()
    
#         if tournament:
#             # Kullanıcıyı turnuvadan çıkar
#             await self.remove_player_from_tournament(tournament)
            
#             # Katılımcı sayısını veritabanından sorgula
#             participant_count = await self.get_participant_count(tournament)
            
#             if participant_count == 0:
#                 # Eğer turnuvada hiç katılımcı yoksa, turnuvayı sil
#                 await self.delete_tournament(tournament)
#                 await self.send(
#                     text_data=json.dumps(
#                         {"message": f"The tournament '{tournament.tournament_name}' has been deleted because there are no participants."}
#                     )
#                 )

#         await super().disconnect(close_code)
#         await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
#         print(f"Disconnected: {self.channel_name}, code: {close_code}")

#     async def receive(self, text_data):
#         data = json.loads(text_data)
#         action = data.get("action", None)

#         if action == "create_tournament":
#             creator_alias = data.get("creator_alias")
#             tournament_name = data.get("tournament_name")

#             if await self.is_user_in_any_tournament():
#                 await self.send(
#                     text_data=json.dumps(
#                         {
#                             "message": "You are already a participant in another tournament. You cannot create a new tournament."
#                         }
#                     )
#                 )
#                 await self.close()
#                 return

#             tournament = await self.create_tournament(creator_alias, tournament_name)
#             if not tournament:
#                 return
#             if isinstance(tournament, str):  # Hata mesajı dönüyorsa
#                 if self.channel_name:
#                     await self.send(
#                         text_data=json.dumps(
#                             {"message": tournament}  # Bu, hata mesajını döndürecek
#                         )
#                     )
#                 await self.close()
#             elif tournament:
#                 await self.send(
#                     text_data=json.dumps(
#                         {
#                             "message": f"Tournament '{tournament_name}' created by {creator_alias}"
#                         }
#                     )
#                 )
#             else:
#                 await self.send(
#                     text_data=json.dumps(
#                         {
#                             "message": "An unknown error occurred while creating the tournament."
#                         }
#                     )
#                 )

#         elif action == "leave_tournament":
#             tournament = await self.get_user_tournament()
#             if not tournament:
#                 await self.send(
#                     text_data=json.dumps({"message": "You are not in any tournament."})
#                 )
#                 return
            
#             # Oyuncuyu turnuvadan çıkar
#             await self.remove_player_from_tournament(tournament)

#             still_in_tournament = await self.get_user_tournament()

#             if still_in_tournament:
#                 await self.send(
#                     text_data=json.dumps(
#                         {"message": "An error occurred while leaving the tournament."}
#                     )
#                 )
#             else:
#                 await self.send(
#                     text_data=json.dumps(
#                         {"message": f"You have left the tournament '{tournament.tournament_name}'."}
#                     )
#                 )
#             if tournament.participant_count == 0:
#                 await self.delete_tournament(tournament)
#                 await self.send(
#                     text_data=json.dumps(
#                         {"message": f"The tournament '{tournament.tournament_name}' has been deleted because there are no participants."}
#                     )
#                 )
#             else:
#                 await self.send(
#                     text_data=json.dumps(
#                         {"message": f"You have left the tournament '{tournament.tournament_name}'."}
#                     )
#                 )

#         elif action == "join_tournament":
#             player_alias = data.get("player_alias")
#             tournament_name = data.get("tournament_name")

#             if await self.is_user_in_any_tournament():
#                 await self.send(
#                     text_data=json.dumps(
#                         {
#                             "message": "You are already a participant in another tournament. You cannot join a new tournament."
#                         }
#                     )
#                 )
#                 await self.close()
#                 return

#             tournament = await self.get_tournament_by_name(tournament_name)
#             if tournament:
#                 if await self.get_participant_count(tournament) < 4:
#                     participant = await self.add_player_to_tournament(
#                         tournament, player_alias
#                     )

#                     if participant:
#                         await self.send(
#                             text_data=json.dumps(
#                                 {
#                                     "message": f"User with alias '{player_alias}' joined the tournament '{tournament_name}'."
#                                 }
#                             )
#                         )
#                     else:
#                         await self.send(
#                             text_data=json.dumps(
#                                 {
#                                     "message": f"Could not add player to the tournament '{tournament_name}'."
#                                 }
#                             )
#                         )
#                         await self.close()
#                 else:
#                     await self.send(
#                         text_data=json.dumps(
#                             {"message": f"Tournament '{tournament_name}' not found."}
#                         )
#                     )
#                     await self.close()
#             else:
#                 await self.send(
#                     text_data=json.dumps(
#                         {
#                             "message": "O isimde Turnuva yokkk"
#                         }
#                     )
#                 )
                

#         elif action == "checkOrStart":
#             tournament = await self.get_user_tournament()
#             if tournament:
#                 participant_count = await self.get_participant_count(tournament)
#                 print(participant_count)
#                 if participant_count == 2:
#                         # Send the signal to the frontend to start the game
#                     await self.send(text_data=json.dumps({
#                         'action': 'start_game',
#                         'message': 'Tournament is ready. Starting the game!'
#                     }))
#                 else:
#                     await self.send(text_data=json.dumps({
#                         'message': f'Tournament is not ready. {participant_count} players present.'
#                     }))
#             else:
#                 await self.send(text_data=json.dumps({
#                     'message': 'You are not part of any tournament.'
#                 }))


#     async def create_tournament(self, creator_alias, tournament_name):
#         if await database_sync_to_async(
#             Tournament.objects.filter(tournament_name=tournament_name).exists
#         )():
#             await self.send(
#                 text_data=json.dumps(
#                     {"error": "Tournament with this name already exists"}
#                 )
#             )
#             await self.close(code=4000)  # Bağlantıyı kapat
#             return None

#         try:
#             # Create the tournament
#             tournament = await database_sync_to_async(Tournament.objects.create)(
#                 creator_alias=creator_alias, tournament_name=tournament_name
#             )

#             # Add the creator as a participant
#             await database_sync_to_async(TournamentParticipant.objects.create)(
#                 user=self.user, tournament=tournament, alias=creator_alias
#             )

#             # Send success message if the connection is still open
#             if self.channel_name:
#                 await self.send(
#                     text_data=json.dumps(
#                         {
#                             "message": f"Tournament {tournament_name} created successfully."
#                         }
#                     )
#                 )

#             return tournament

#         except Exception as e:
#             print(f"Error while creating tournament: {e}")
#             # Send error message if the connection is still open
#             if self.channel_name:
#                 await self.send(
#                     text_data=json.dumps(
#                         {"error": "An error occurred while creating the tournament"}
#                     )
#                 )
#             await self.close()  # Close the WebSocket connection
#             return None

#     @database_sync_to_async
#     def get_tournament_by_name(self, tournament_name):
#         return Tournament.objects.filter(tournament_name=tournament_name).first()

#     @database_sync_to_async
#     def add_player_to_tournament(self, tournament, player_alias):
#         try:
#             # Turnuvada bu alias'a sahip bir katılımcı var mı diye kontrol et
#             existing_participant = TournamentParticipant.objects.filter(
#                 alias=player_alias, tournament=tournament
#             ).first()

#             if existing_participant:
#                 # Eğer alias zaten varsa, hata mesajı gönder
#                 return None

#             existing_user_participant = TournamentParticipant.objects.filter(
#                 user=self.user, tournament=tournament
#             ).first()

#             if existing_user_participant:
#                 return None

#             # Katılımcı kullanıcıyı oturum açmış kullanıcıyla eşleştir
#             participant = TournamentParticipant.objects.create(
#                 user=self.user,  # Burada oturum açmış kullanıcıyı alıyoruz
#                 tournament=tournament,
#                 alias=player_alias,
#             )

#             return participant  # Katılım başarıyla oluşturuldu

#         except Exception as e:
#             print(f"Error while adding player to tournament: {e}")
#             return None

#     @database_sync_to_async
#     def get_participant_by_alias(self, player_alias, tournament):
#         # Turnuvada bu alias'a sahip bir katılımcı var mı diye kontrol et
#         return TournamentParticipant.objects.filter(
#             alias=player_alias, tournament=tournament
#         ).first()

#     @database_sync_to_async
#     def is_user_in_any_tournament(self):
#         # Kullanıcının başka bir turnuvaya katılıp katılmadığını kontrol et
#         return TournamentParticipant.objects.filter(user=self.user).exists()

#     @database_sync_to_async
#     def get_user_tournament(self):
#         participant = TournamentParticipant.objects.filter(user=self.user).first()
#         return participant.tournament if participant else None

#     @database_sync_to_async
#     def remove_player_from_tournament(self, tournament):
#         TournamentParticipant.objects.filter(user=self.user, tournament=tournament).delete()

#     @database_sync_to_async
#     def delete_tournament(self, tournament):
#         # Turnuvayı sil
#         tournament.delete()

#     @database_sync_to_async
#     def get_participant_count(self, tournament):
#         return TournamentParticipant.objects.filter(tournament=tournament).count()
