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
        self.next_game = False
        if not self.user.is_authenticated:
            await self.close()
            return

        # URL query params içinden mod ve alias bilgisini al
        query_params = parse_qs(self.scope["query_string"].decode())
        is_tournament_mode = query_params.get("tournament_mode", ["false"])[0] == "true"
        alias = query_params.get("alias", [None])[0] 
        print(f"📥 Gelen alias: {alias}")

        if alias:
            # Alias'ı güncelle ve kaç satır değiştiğini kontrol et
            updated_count = await database_sync_to_async(lambda: User.objects.filter(id=self.user.id).update(alias=alias))()
            print(f"🔄 Güncellenen kullanıcı sayısı: {updated_count}")
            
            # Kullanıcı nesnesini güncelle
            self.user.alias = alias
            print(f"📝 Kullanıcı alias güncellendi: {self.user.alias}")

        # Güncellenen alias'ı doğrulamak için tekrar veritabanından çek
        db_alias = await database_sync_to_async(lambda: User.objects.filter(id=self.user.id).values_list("alias", flat=True).first())()
        print(f"📌 Veritabanından alınan alias: {db_alias}")
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
            await asyncio.sleep(0.1)  # Alias güncellenmesi için kısa bir bekleme

            if self.room_group_name.startswith("tournament_"):
                # Turnuva modundaysa alias'ları al
                player_aliases = await database_sync_to_async(
                    lambda: list(User.objects.filter(id__in=[p.id for p in room["players"]]).values_list("alias", flat=True))
                )()
                if all(player_aliases):  # Eğer alias'lar varsa
                    await self.send_player_info()
            else:
                # 1v1 modundaysa direkt `send_player_info` çağır
                await self.send_player_info()

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "game_message",
                    "message": "Both players connected. Starting game...",
                },
            )
            await asyncio.sleep(1)
            asyncio.create_task(self.start_game())

    async def send_player_info(self):
        global rooms
        room = rooms.get(self.room_group_name, None)
        players = room["players"]

        if len(players) == 2:
            print(f"DEBUG: Left Type: {players[0].alias}, Right Type: {players[1].alias}")
            left_player = players[0]
            right_player = players[1]

            if self.room_group_name.startswith("tournament_"):
                left_player_db = await database_sync_to_async(User.objects.get)(id=left_player.id)
                right_player_db = await database_sync_to_async(User.objects.get)(id=right_player.id)
                
                print(f"🔍 Database’ten çekildi: {left_player_db.alias} - {right_player_db.alias}")

                # Sadece string olarak alias gönder
                left_name = left_player_db.alias  
                right_name = right_player_db.alias  
            else:
                left_name = left_player.nick
                right_name = right_player.nick

            print(f"📢 Gönderilen Oyuncu Bilgileri: Left = {left_name}, Right = {right_name}")

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "player_info",
                    "left": left_name,   # ✅ Artık sadece string veri gönderiyoruz
                    "right": right_name,  # ✅
                }
            )

        
       # print(f"🎮 Left Player: {left_name}, Right Player: {right_name}")

    async def player_info(self, event):
        await self.send(text_data=json.dumps(event))


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

            if is_tournament:
                await database_sync_to_async(lambda: User.objects.filter(id=self.user.id).update(alias=""))()

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
                    winner_message = " 🎉 You are the TOURNAMENT CHAMPION! 🏆"

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
        action = text_data_json.get("action")
        global rooms
        room = rooms[self.room_group_name]
        game_state = room["game_state"]

        if action == "getAlias":
            alias = text_data_json.get("alias")
            user_id = self.scope["user"].id

            # Alias'ı güncelle ve kullanıcı nesnesine işle
            await database_sync_to_async(lambda: User.objects.filter(id=user_id).update(alias=alias))()
            self.user.alias = alias  # Cache içindeki nesneyi güncelle

            # İki oyuncunun da alias'ı var mı kontrol et
            player_ids = [p.id for p in room.get("players", [])]  # Hata almamak için güvenli kontrol
            player_aliases = await database_sync_to_async(
                lambda: list(User.objects.filter(id__in=player_ids).values_list("alias", flat=True))
            )()

            if len(player_aliases) == 2 and all(player_aliases):  # İki oyuncu da alias aldı mı?
                await self.send_player_info()
            
            print(f"🎮 Alias kontrol: Kullanıcı: {self.user}, Alias: {alias}")

        elif action == "next_game":
            self.next_game = True
        
        elif action == "leave_tournament":
            self.next_game = False

        if "move" in text_data_json:
            direction = text_data_json["move"]
            player = game_state["players"].get(self.player_id, {})
            if direction == "up" and player.get("y", 0) > 0:
                player["y"] -= 5
            elif direction == "down" and player.get("y", 0) < 520:  # Paddle height
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
            if game_state["scores"]["player1"] == 11:
                await self.end_game("player1")
                print("Player 1 won the game.")
                break
            elif game_state["scores"]["player2"] == 11:
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
            winner_message = " 🎉 You are the TOURNAMENT CHAMPION! 🏆"

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
        if not getattr(self, "next_game", False):
            await database_sync_to_async(lambda: User.objects.filter(id__in=[winner_user.id, loser_user.id]).update(alias=""))()
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
