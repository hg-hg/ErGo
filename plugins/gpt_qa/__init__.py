from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.application.message.elements.internal import Plain
from graia.application.message.elements.internal import Image as graiaImage
from graia.application.message.chain import MessageChain
from graia.application.group import Group, Member
from mirai_core import judge
from mirai_core import Get

import re
import time
import os
from extensions.cpm_lm.sample import sample
from PIL import Image, ImageDraw, ImageFont
import textwrap
import uuid

__plugin_name__ = '二狗QA'
__plugin_usage__ = '召唤bot使用模型推理'

bcc = Get.bcc()


def _draw_multiple_line_text(image, text, font, text_color, text_start_height, width):
    '''
    From unutbu on [python PIL draw multiline text on image](https://stackoverflow.com/a/7698300/395857)
    '''
    draw = ImageDraw.Draw(image)
    image_width, image_height = image.size
    y_text = text_start_height
    lines = textwrap.wrap(text, width=width)
    for line in lines:
        line_width, line_height = font.getsize(line)
        draw.text(((image_width - line_width) / 2, y_text),
                  line, font=font, fill=text_color)
        y_text += line_height


def text_to_img(text):

    # image_width
    width, height = 300, 200
    image = Image.new('RGB', (width, height), color=(0, 0, 0))
    fontsize = 12  # starting font size
    font = ImageFont.truetype(
        "/ErGo/plugins/gpt_qa/ChaoZiSheGuoFengRanSongJian-2.ttf", fontsize)

    text_color = (200, 200, 200)
    text_start_height = 0
    _draw_multiple_line_text(
        image, text, font, text_color, text_start_height, width=width//fontsize)

    img_filename = str(uuid.uuid4()) + '.png'
    image.save(img_filename)
    return img_filename


def cut_by_symbol(sentence):
    symbols = [',', '，', '.', '。', '《', '》', '?', '？', '!', "！"]
    symbol_idx = [sentence.rfind(symbol) for symbol in symbols]
    cut_idx = max(symbol_idx)
    if cut_idx == -1:
        return sentence, ''
    else:
        cutted_segment = sentence[cut_idx:]
        return sentence[:cut_idx], cutted_segment


@bcc.receiver(GroupMessage, headless_decoraters=[judge.group_check(__name__)])
async def gpt_qa(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member):
    if message.asDisplay().startswith(('二狗')):
        try:
            msg = message.asDisplay()
            query = msg[2:]
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("稍等 让我想想"),
            ]))

            # 推理
            _begin_time = time.time()
            answer = sample(query, length=100)[0]
            _original_len = len(answer)

            # 截断最后一个符号
            answer, answer_cutted = cut_by_symbol(answer)
            _cutted_len = len(answer)
            _time_taken = int(time.time() - _begin_time)

            # 生成返回输出
            response = answer + '。 \n'
            response_meta = f"\n耗时: {_time_taken}s; 句长(截断前/后):{_original_len}/{_cutted_len}; 截断长度:{_original_len - _cutted_len};"
            response_meta += f"\n截断内容: {answer_cutted}"
            img_response_path = text_to_img(response)

            # 返回信息
            await app.sendGroupMessage(group, MessageChain.create([
                graiaImage.fromLocalFile(img_response_path),
                Plain(response_meta)
            ]))

            # 删除生成输出文件
            os.remove(img_response_path)

        except ValueError:
            return
