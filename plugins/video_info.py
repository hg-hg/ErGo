from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.application.message.elements.internal import Plain, Image
from graia.application.message.chain import MessageChain
from graia.application.group import Group, Member
from mirai_core import judge
from mirai_core import Get

import re
import aiohttp

__plugin_name__ = 'B站视频信息查看'
__plugin_usage__ = '发送任意av/BV号获取视频信息'

bcc = Get.bcc()


@bcc.receiver(GroupMessage, headless_decoraters=[judge.group_check(__name__)])
async def video_info(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member):
    msg = message.asDisplay()
    id_type, num = detect_vid(msg)

    if id_type != '':
        url = f'https://api.bilibili.com/x/web-interface/view?{id_type}={num}'
        async with aiohttp.request("GET", url) as r:
            get = await r.json()

        if 'data' in get:
            data = get['data']
            during = '{}分{}秒'.format(data['duration'] // 60, data['duration'] % 60)

            await app.sendGroupMessage(group, MessageChain.create([
                Image.fromNetworkAddress(get['data']['pic']),
                Plain(f"\n标题:{data['title']}"),
                Plain(f"\nUp主:{data['owner']['name']}"),
                Plain(f"\n视频时长:{during}"),
                Plain(f"\nav号:{data['aid']}"),
                Plain(f"\nbv号:{data['bvid']}"),
                Plain(f"\n链接:https://bilibili.com/video/{data['bvid']}")
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"搜索不到视频信息"),
            ]))


def detect_vid(text):

    pat_aid = 'av[1-9][0-9]{0,8}'
    pat_bid = 'bv[0-9a-z]{10}'

    if re.match(pat_aid, text, re.I):
        id_type = 'aid'
        num = re.sub('av', '', text, flags=re.I)
    elif re.match(pat_bid, text, re.I):
        id_type = 'bvid'
        num = text
    else:
        id_type = ''
        num = ''

    return id_type, num


"""
av号             av
bv号     
含av链接
含bv链接
移动端短链接


"""