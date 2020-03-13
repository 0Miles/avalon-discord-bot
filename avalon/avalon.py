import asyncio
import discord
from discord.ext import commands
from discord.ext.commands import guild_only
from asyncio import TimeoutError

from .enums import Position, Faction
from .constant import POSITION_NAME_LIST, POSITION_IMAGE_LIST, EMOJI, QEMOJI
from .dialog import Dialog
from .player import Player
from .game import Game

class Avalon(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    def init_dialog(self, dialog):
        dialog.bot = self.bot
        dialog.name = "Avalon"
        dialog.icon_url = "https://cdn.discordapp.com/attachments/485384215420993537/667991466018209812/151905.jpg"
        dialog.color = 0x73a936
        dialog.update_embed()

    async def send_notice(self, ctx, title, content, delete_after=None):
        dialog = Dialog(title=title, content=content)
        self.init_dialog(dialog)

        return await ctx.send(embed=dialog(), delete_after=delete_after)

    async def sign_up(self, ctx, user_dict = {}):
        title = "開始新遊戲"
        content = "按 👍 加入遊戲\n參加者到齊後，由遊戲發起人 ``{}#{}`` 按下 ✅ 開始。\n\n*(至少需有 4 人才能開始遊戲)*\n".format(ctx.author.display_name, ctx.author.discriminator)
        dialog = Dialog(
            title=title,
            content=content,
            buttons=["👍"],
            valid={"✅": [ctx.author.id]}
            )
        self.init_dialog(dialog)
        dialog.embed.add_field(name="目前人數", value=len(user_dict))
        if len(user_dict) > 0:
            dialog.embed.add_field(
                    name="參加名單",
                    value=str.join("\n", ["``{}``".format(user_dict[key].display_name) for key in user_dict]),
                    inline=False
                    )
            

        await dialog.send_dialog_message(ctx)

        while True:
            response_reaction, response_user = await dialog.wait_respond()
            response_emoji = str(response_reaction.emoji)
            if response_emoji == "✅":
                break

            if response_emoji == "👍":
                try:
                    user_dict.pop(response_user.id)
                except:
                    user_dict[response_user.id] = response_user

            await dialog.reset_button(response_reaction, response_user)

            dialog.embed.clear_fields()
            dialog.embed.add_field(name="目前人數", value=len(user_dict))
            if len(user_dict) > 0:
                dialog.embed.add_field(
                    name="參加名單",
                    value=str.join(", ", ["``{}``".format(user_dict[key].display_name) for key in user_dict]),
                    inline=False
                    )
            await dialog.edit()

            if len(user_dict) > 3 and len(user_dict) < 11:
                await dialog.add_button("✅")
            else:
                try:
                    await dialog.remove_button("✅")
                except:
                    pass

        await dialog.close()
        return user_dict

    async def option_lake(self, ctx):
        title = "開始新遊戲"
        content = "是否啟用湖中女神?"
        dialog = Dialog(
            title=title,
            content=content,
            buttons=["✅", "❎"],
            valid=ctx.author.id
            )
        self.init_dialog(dialog)

        await dialog.send_dialog_message(ctx)

        response_reaction, response_user = await dialog.wait_respond()
        if str(response_reaction.emoji) == "✅":
            return True
        else:
            return False
        
        await dialog.close()

    async def new_game(self, ctx, user_dict = {}):
        user_dict = await self.sign_up(ctx, user_dict)
        lady_of_the_lake_enabled = await self.option_lake(ctx)
        self.games[ctx.channel.id] = Game(ctx, user_dict, lady_of_the_lake_enabled)
        return self.games[ctx.channel.id]

    async def send_game_board(self, game):
        dialog = Dialog()
        self.init_dialog(dialog)

        player_string_list = []
        for i in range(0, len(game.player_list)):
            player_temp = game.player_list[i]

            player_info = EMOJI[i+1] + " "
            if game.stage == 2 or game.stage == 1 and player_temp.faction == Faction.Mordred:
                player_info += EMOJI[player_temp.faction]

            if game.leader.index == i and game.stage == 0:
                player_info += EMOJI["crown"] + " "

            player_info += player_temp.user.display_name + " "
            if game.stage == 2 or game.stage == 1 and player_temp.faction == Faction.Mordred:
                player_info += "(" + player_temp.position_name + ")"
            
            if game.lady_of_the_lake_enabled and game.stage == 0:
                if game.holding_lady.index == i:
                    player_info += EMOJI["lake"]
                elif player_temp.lake_target is not None:
                    player_info += EMOJI["laked"]

            if game.assassin is not None and game.assassin.assassinate_target is not None:
                if player_temp.index == i and player_temp.index == game.assassinate_target.index:
                    player_info += EMOJI["knife"]

            player_string_list.append(player_info)

        dialog.embed.add_field(name="玩家", value=str.join("\n", player_string_list), inline=False)
        dialog.embed.add_field(name="任務狀態", value=game.status, inline=False)
        dialog.embed.add_field(name="投票次數記錄", value=game.vote_status, inline=False)

        return await dialog.send_dialog_message(game.ctx)

    async def send_position_info(self, game, player):
        dialog = Dialog(thumbnail_url=player.position_image)
        self.init_dialog(dialog)
        dialog.embed.add_field(
            name="你的身份", value=player.position_name, inline=False)

        desc = "``🔵 亞瑟的忠臣`` ``🔴 莫德雷德的爪牙``"
        if player.position == Position.Percival:
            desc += " ``🟣 梅林或魔甘娜``"
        dialog.embed.add_field(name="符號說明", value=desc, inline=False)

        player_string_list = []

        for i in range(0, len(game.player_list)):
            player_temp = game.player_list[i]
            player_info = EMOJI[i+1] + " "
            if player.position == Position.Percival and (player_temp.position == Position.Merlin or player_temp.position == Position.Morcana) and (player.lake_target is None or player.lake_target.index != i):
                player_info += EMOJI["purple"] + " "
            elif player.lake_target is not None and player.lake_target.index == i and game.lady_of_the_lake_enabled or player.position == Position.Merlin and player_temp.position != Position.Mordred and player_temp.faction == Faction.Mordred or player.position != Position.Oberon and player_temp.position != Position.Oberon and player_temp.faction == Faction.Mordred and player.faction == Faction.Mordred:
                player_info += EMOJI[player_temp.faction] + " "

            player_info += player_temp.user.display_name
            player_string_list.append(player_info)

        dialog.embed.add_field(name="角色視野", value=str.join("\n", player_string_list), inline=False)

        await dialog.send_dialog_message(player.user)

    async def send_all_player_position_info(self, game):
        for player in game.player_list:
            await self.send_position_info(game, player)

    async def stage_appoint(self, game):
        num = game.number_of_people
        dialog = Dialog(
            title="第 {} 輪指派任務".format(game.round),
            content="由 {} 指派 {} 員玩家參與此次任務".format(game.leader.tag, num),
            buttons=[EMOJI[i+1] for i in range(0,game.total_player_count)],
            valid=game.leader.user.id,
            thumbnail_url=game.leader.user.avatar_url
        )
        self.init_dialog(dialog)

        await dialog.send_dialog_message(game.ctx)

        appoint_player_dict = {}

        while True:
            response_reaction, response_user = await dialog.wait_respond()
            response_emoji = str(response_reaction.emoji)
            if response_emoji == "✅" and len(appoint_player_dict) == num:
                break
            else:
                if len(appoint_player_dict) < num:
                    try:
                        appoint_player_dict.pop(QEMOJI[response_emoji])
                    except:
                        appoint_player_dict[QEMOJI[response_emoji]] = game.player_list[QEMOJI[response_emoji] - 1]
                else:
                    appoint_player_dict.pop(QEMOJI[response_emoji], None)

            await dialog.reset_button(response_reaction, response_user)

            dialog.embed.clear_fields()
            if len(appoint_player_dict) > 0:
                dialog.embed.add_field(name="任務名單", value=str.join("\n", [appoint_player_dict[key].tag for key in appoint_player_dict]), inline=False)
            await dialog.edit()

            if len(appoint_player_dict) == num:
                await dialog.add_button("✅")
            else:
                try:
                    await dialog.remove_button("✅")
                except:
                    pass

        await dialog.close()
        return appoint_player_dict

    async def stage_public_vote(self, game, appoint_player_dict):
        num = game.number_of_people
        title = "第 {} 輪投票表決".format(game.round)
        content = "是否同意由 {} 指派的這 {} 員玩家參與此次任務".format(game.leader.tag, num)
        player_id_list = [player.user.id for player in game.player_list]
        player_string_list = []
        player_vote_dict = {}
        agree_count = 0

        dialog = Dialog(
            title=title,
            content=content,
            buttons=["✅", "❎"],
            valid=player_id_list
        )
        self.init_dialog(dialog)

        dialog.embed.add_field(name="任務名單", value=str.join("\n", [appoint_player_dict[key].tag for key in appoint_player_dict]), inline=False)

        await dialog.send_dialog_message(game.ctx)

        while len(player_id_list) > 0:
            response_reaction, response_user = await dialog.wait_respond()
            player_id_list.remove(response_user.id)
            player_vote_dict[response_user.id] = str(response_reaction.emoji)
            if str(response_reaction.emoji) == "✅":
                agree_count += 1

            await dialog.reset_button(response_reaction, response_user)

            dialog.embed.clear_fields()
            dialog.embed.add_field(name="任務名單", value=str.join("\n", [appoint_player_dict[key].tag for key in appoint_player_dict]), inline=False)

            player_string_list = []
            for i in range(0, len(game.player_list)):
                player_temp = game.player_list[i]
                player_vote_dict[player_temp.user.id] = player_vote_dict.pop(player_temp.user.id, "")
                player_info = "`` " + EMOJI[i+1] + player_temp.user.display_name + " `` " + player_vote_dict[player_temp.user.id]
                player_string_list.append(player_info)

            dialog.embed.add_field(name="投票狀況", value=str.join("\n", player_string_list), inline=False)
            await dialog.edit()

        flag = True
        if agree_count > game.total_player_count - agree_count:
            dialog.embed.add_field(name="投票結果", value="通過", inline=False)
        else:
            dialog.embed.add_field(name="投票結果", value="否決", inline=False)
            flag = False
        await dialog.edit()
        return flag

    async def private_vote(self, game, player):
        buttons = ["✅"]
        title = "第 {} 輪任務投票".format(game.round)
        content = "您是 " + player.position_name + ", 請投任務成功"
        if player.faction == Faction.Mordred:
            buttons.append("❎")
            content += "或任務失敗"
            if game.round == 4 and game.round4need2fail:
                content += "\n*此輪需要2張失敗票*"
        
        dialog = Dialog(
            title=title,
            content=content,
            buttons=buttons,
            valid=player.user.id,
            thumbnail_url=player.position_image
        )
        self.init_dialog(dialog)

        await dialog.send_dialog_message(player.user)

        response_reaction, response_user = await dialog.wait_respond()
        response_emoji = str(response_reaction.emoji)
        dialog.content = "已完成投票" + response_emoji
        dialog.update_embed()
        await dialog.edit()

        return response_emoji=="✅"

    async def stage_private_vote(self, game, appoint_player_dict):
        num = game.number_of_people
        title = "任務進行中"
        content = "請等待由 {} 指派的 {} 員玩家完成任務投票".format(game.leader.tag, num)

        public_message = await self.send_notice(game.ctx, title, content)
        
        vote_list = []
        for key in appoint_player_dict:
            vote_list.append(self.private_vote(game, game.player_list[key-1]))
            
        done, pending = await asyncio.wait(vote_list)

        fail_num = [task.result() for task in done].count(False)

        flag = True
        if game.round == 4 and game.round4need2fail and fail_num < 2 or fail_num < 1:
            title = "第 {} 輪任務成功".format(game.round)
        else:
            title = "第 {} 輪任務失敗".format(game.round)
            flag = False
            
        if fail_num == 0:
            content = "這次任務沒有失敗票"
        else:
            content = "這次任務有 {} 張失敗票".format(fail_num)

        embed = discord.Embed(title=title, description=content, color=0x73a936)
        await public_message.edit(embed=embed)
        return flag

    async def stage_lake(self, game):
        title = "湖中女神出現"
        content = "由 {} 使用第 {} 次湖中女神，你要查驗的對象是?".format(game.holding_lady.tag, game.lake_count + 1)
        buttons = []
        for i in range(0, len(game.player_list)):
            if game.player_list[i].lake_target is None and game.holding_lady.index != i:
                buttons.append(EMOJI[i+1])

        dialog = Dialog(
            title=title,
            content=content,
            image_url="https://cdn.discordapp.com/attachments/485384215420993537/669723922006147072/tumblr_og002iAun71uwjxiho1_640.jpg",
            buttons=buttons,
            valid=game.holding_lady.user.id,
            thumbnail_url=game.holding_lady.user.avatar_url
        )
        self.init_dialog(dialog)
        await dialog.send_dialog_message(game.ctx)

        response_reaction, response_user = await dialog.wait_respond()
        response_emoji = str(response_reaction.emoji)

        dialog.content = "{} 使用湖中女神查驗了 `` {}{} ``".format(
            game.holding_lady.tag,
            response_emoji,
            game.player_list[QEMOJI[response_emoji] - 1].user.display_name
            )

        dialog.update_embed()
        await dialog.edit()

        game.holding_lady.lake_target = game.player_list[QEMOJI[response_emoji] - 1]
        await self.send_position_info(game, game.holding_lady)
        game.holding_lady = game.holding_lady.lake_target
        game.lake_count += 1

    async def stage_assassinate(self, game):
        title = "刺殺階段"
        content = "由刺客 {} 選擇剌殺對象，若成功刺殺梅林，則由紅方反敗為勝".format(game.assassin.tag)

        buttons = []
        for i in range(0, len(game.player_list)):
            if game.player_list[i].faction == Faction.Arthur:
                buttons.append(EMOJI[i+1])
        
        dialog = Dialog(
            title=title,
            content=content,
            buttons=buttons,
            valid=game.assassin.user.id,
            thumbnail_url=game.assassin.user.avatar_url
        )
        self.init_dialog(dialog)
        await dialog.send_dialog_message(game.ctx)

        response_reaction, response_user = await dialog.wait_respond()
        response_emoji = str(response_reaction.emoji)
        game.assassin.assassinate_target = game.player_list[QEMOJI[response_emoji] - 1]

        dialog.content = "刺客 {} 剌殺了 {}\n{} 的身分為: ``{}``".format(
            game.assassin.tag,
            game.assassin.assassinate_target.tag,
            game.assassin.assassinate_target.tag,
            game.assassin.assassinate_target.position_name)
            
        dialog.update_embed()
        await dialog.edit()

    async def stage_ending(self, game):
        if game.vote_count > 4 or game.round_status.count("fail") > 2:
            #紅方獲勝
            game.stage = 2
            await self.send_game_board(game)
        else:
            game.stage = 1
            await self.send_game_board(game)
            await self.stage_assassinate(game)  # 刺殺階段
            game.stage = 2
            await self.send_game_board(game)

    async def stage_restart(self, game):
        title = "遊戲結束，{}獲勝".format("藍方" if game.result == Faction.Arthur else "紅方")
        content = "再來一局?"
        dialog = Dialog(
            title=title,
            content=content,
            image_url=POSITION_IMAGE_LIST[Position.Merlin] if game.result == Faction.Arthur else POSITION_IMAGE_LIST[Position.Mordred],
            buttons=["✅", "❎"],
            valid=game.ctx.author.id
            )
        self.init_dialog(dialog)

        await dialog.send_dialog_message(game.ctx)

        try:
            response_reaction, response_user = await dialog.wait_respond()
        except TimeoutError:
            raise
        else:
            if str(response_reaction.emoji) == "✅":
                return True
            else:
                return False
        finally:
            await dialog.close()
        
    async def game_loop(self, game):
        while game is not None:
            game.deal()  # 發身分牌
            await self.send_all_player_position_info(game)  # 私訊角色資訊
            while True:
                await self.send_game_board(game)

                if game.lady_of_the_lake_enabled and game.round > 2 and game.lake_count < 3 and game.total_player_count - game.lake_count > 1:
                    await self.stage_lake(game) # 湖中女神階段
                
                appoint_player_dict = await self.stage_appoint(game)
                agree_appoint = await self.stage_public_vote(game, appoint_player_dict)
                if agree_appoint:
                    result = await self.stage_private_vote(game, appoint_player_dict)
                    if result:
                        game.round_status[game.round-1] = "success"
                    else:
                        game.round_status[game.round-1] = "fail"
                    game.vote_count = 0
                    if game.round_status.count("success") > 2 or game.round_status.count("fail") > 2:
                        break
                    game.next_round()
                else:
                    game.vote_count += 1
                    if game.vote_count > 4: 
                        break

                game.next_leader()
            await self.stage_ending(game)
            
            if await self.stage_restart(game):
                game = await self.new_game(game.ctx, game.user_dict)
            else:
                self.games.pop(game.ctx.channel.id)
                game = None

    @commands.command()
    @commands.guild_only()
    async def avalon(self, ctx, arg):
        if arg == "start":
            try:
                self.games[ctx.channel.id]
            except KeyError:
                try:
                    self.games[ctx.channel.id] = "creating"
                    await self.game_loop(await self.new_game(ctx, {ctx.author.id: ctx.author}))
                except TimeoutError:
                    if ctx.channel.id in self.games:
                        await self.send_notice(ctx, "遊戲已關閉", "過長時間無人回應")
                except:
                    await self.send_notice(ctx, "發生錯誤", "建立遊戲失敗")

                self.games.pop(ctx.channel.id, None)
            else:
                await self.send_notice(ctx, "遊戲正在進行", "此頻道中目前有正在進行的遊戲")
                
        elif arg == "stop":
            try:
                self.games.pop(ctx.channel.id)
                await self.send_notice(ctx, "遊戲已關閉", "已清除此頻道中所有正在進行的遊戲")
            except KeyError:
                await self.send_notice(ctx, "遊戲已關閉", "沒有正在進行的遊戲")
        
