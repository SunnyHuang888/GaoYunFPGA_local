"""Generate editable SVG and PNG architecture diagrams; source repo is read-only.
Requires Pillow and Windows Microsoft YaHei fonts. Run from any directory.
"""
from pathlib import Path
from html import escape
import math
from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent
BLUE, GREEN, ORANGE, PURPLE = '#2563a5', '#18785e', '#b46a20', '#7950a0'
INK, MUTED = '#17324d', '#52677d'


class Diagram:
    def __init__(self, title, desc):
        self.im = Image.new('RGB', (1600, 1200), '#f7f9fc')
        self.d = ImageDraw.Draw(self.im)
        self.svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">',
                    f'<title>{escape(title)}</title><desc>{escape(desc)}</desc>',
                    '<rect width="1600" height="1200" fill="#f7f9fc"/>']
        self.text(40, 25, title, 36, INK, True)
        self.text(40, 82, desc, 20)

    def text(self, x, y, s, size=21, color=MUTED, bold=False):
        font = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc', size)
        assert x + self.d.textlength(s, font=font) < 1590, s
        self.d.text((x, y), s, font=font, fill=color)
        self.svg.append(f'<text x="{x}" y="{y+size}" font-family="Microsoft YaHei, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(s)}</text>')

    def box(self, x, y, w, h, fill='#ffffff', stroke='#cbd7e3', dash=False):
        self.d.rounded_rectangle((x,y,x+w,y+h), radius=12, fill=fill, outline=stroke, width=2)
        self.svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="2"'+(' stroke-dasharray="7 5"' if dash else '')+'/>')

    def card(self, x,y,w,h,title,lines,color=BLUE,fill='#ffffff'):
        self.box(x,y,w,h,fill,color)
        self.text(x+15,y+12,title,24,color,True)
        size, start, step = (19,48,27) if len(lines)>3 and h<180 else (20,53,31)
        for i,line in enumerate(lines):
            font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',size)
            assert self.d.textlength(line,font=font)<w-26,(title,line)
            self.text(x+15,y+start+i*step,line,size)

    def arrow(self, pts, color=BLUE, dash=False):
        # Dashed segments rendered in both formats.
        for (x0,y0),(x1,y1) in zip(pts,pts[1:]):
            length=math.hypot(x1-x0,y1-y0)
            if dash:
                for k in range(0,int(length),15):
                    a=k/length;b=min(k+8,length)/length
                    self.d.line((x0+(x1-x0)*a,y0+(y1-y0)*a,x0+(x1-x0)*b,y0+(y1-y0)*b),fill=color,width=3)
            else:self.d.line((x0,y0,x1,y1),fill=color,width=3)
        x,y=pts[-1];px,py=pts[-2];a=math.atan2(y-py,x-px)
        wing=[(x,y),(x-12*math.cos(a-.45),y-12*math.sin(a-.45)),(x-12*math.cos(a+.45),y-12*math.sin(a+.45))]
        self.d.polygon(wing,fill=color)
        points=' '.join(f'{x},{y}' for x,y in pts)
        self.svg.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"'+(' stroke-dasharray="8 7"' if dash else '')+'/>')
        self.svg.append('<polygon points="'+' '.join(f'{x:.1f},{y:.1f}' for x,y in wing)+f'" fill="{color}"/>')

    def save(self,name):
        self.im.save(OUT/(name+'.png'))
        (OUT/(name+'.svg')).write_text('\n'.join(self.svg+['</svg>']),encoding='utf8',newline='\n')


def main():
    d=Diagram('高云杯电子琴｜三层系统架构',
              '2026-10-07 · develop / 3c14bb4 · 开发与观测 → FPGA 实时合成 → 板级模拟输出；集成不等于新版上板验收')
    d.box(30,125,1540,185,'#edf3fb','#9ab7d5')
    d.text(50,169,'第一层',21,BLUE,True)
    d.text(50,207,'上位机',29,BLUE,True)
    d.text(50,256,'开发与辅助软件',20,BLUE)
    d.card(260,145,410,145,'状态监视与输入采集  §2.1 / 2.6',
           ['UART STAT / DIAG → 显示与 CSV','USB MIDI → PC 消息采集','电脑不承担正式实时音频合成'],BLUE)
    d.card(700,145,410,145,'Python 参考与生成工具  §2.2–2.4',
           ['DDS / ADSR / 混音参考模型','生成波表、FCW、测试向量','参考音频 / 频谱 / RTL 对照'],BLUE)
    d.card(1140,145,400,145,'仿真与 Gowin EDA  §2.5',
           ['RTL 仿真与检查','综合 → 布局布线 → 时序分析','生成码流，经 JTAG 配置 / 下载'],BLUE)
    d.arrow([(1110,219),(1140,219)],BLUE)
    d.arrow([(1340,290),(1340,365)],BLUE)
    d.text(1145,320,'JTAG：配置 / 下载',19,BLUE)
    d.box(30,365,1540,465,'#eef7f4','#98bcae')
    d.text(50,376,'第二层 · FPGA 实时数字处理',27,GREEN,True)
    d.text(625,381,'60K 正式顶层 · 50 MHz / 48 kHz · reset_sync / pa_en',23,GREEN)
    xs=[55,445,835,1225];w=320
    cards=[('输入适配  §3.2',['按键 → 同步 / 去抖 / 转事件','DIN → 隔离 → R17 UART','31,250 baud · 8N1','midi_input / 字节解析']),
           ('事件缓存  §3.3',['按键本地 FIFO / MIDI 调度','双源轮转仲裁','32 项公共事件 FIFO','64 位事件 · valid / ready']),
           ('事件路由与四槽  §3.4.1',['router → voice_allocator_4','source / channel / note 身份','CC64 → sustain_controller','note_pitch → 32 位基础 FCW']),
           ('波形与包络  §3.4–3.5.3',['piano_triangle_voice × 4','Program 0：V1；1：三角','四槽 ADSR / Velocity','统一 lane_tick 推进样本'])]
    for x,(t,lines) in zip(xs,cards):d.card(x,422,w,170,t,lines,GREEN)
    for x in xs[:-1]:d.arrow([(x+w,505),(x+390,505)],GREEN)
    d.arrow([(1385,592),(1385,640)],GREEN)
    cards2=[('状态计数与 UART  §3.7.1',['来自事件 / 音频各模块的计数','活跃数 / clip / FIFO / 欠载等','状态计数 → UART 文本格式化','U15 → PC：STAT / DIAG']),
            ('串行发送  §3.6.2',['i2s_tx：PCM24 → signed16','32 bit 槽 × 左右声道','LSBJ：WS 低右 / 高左','BCLK / LRCK / DIN']),
            ('逐帧交付  §3.6.1',['polyphonic_pcm_commit','结果保持 → pcm_frame_buffer','req_id 校验 / 过期结果丢弃','play_left / right 保持到装载']),
            ('增益与混音  §3.5.1',['wave × envelope → Q15','voice_gain_q15_candidate × 4','四路 PCM24 → 宽累加 / 饱和','当前核心 L / R 使用同组声部'])]
    for x,(t,lines) in zip(xs,cards2):d.card(x,640,w,170,t,lines,BLUE if x==55 else GREEN)
    for x in xs[2:]:d.arrow([(x,725),(x-70,725)],GREEN)
    d.arrow([(605,640),(605,619),(990,619),(990,640)],BLUE)
    d.text(645,594,'frame_tick → sample_req / req_id → 银行计算',18,BLUE)
    d.arrow([(55,725),(18,725),(18,334),(465,334),(465,290)],BLUE)
    d.text(55,313,'UART 状态回传 → 上位机',18,BLUE)
    d.box(800,851,770,62,'#f4effa','#b89acd')
    d.text(816,857,'138K L 另见专图：40 MHz + Pitch/Mod + HDMI，默认 V1。',19,PURPLE)
    d.text(816,885,'它不包含本图动态双音色；V0197 为精确工程 L5，未 L6。',18,PURPLE)
    d.text(50,859,'FPGA → DAC：BCLK / LRCK / DIN',20,ORANGE)
    d.box(30,929,1540,207,'#fff3e6','#d9af7b')
    d.text(50,957,'第三层',21,ORANGE,True)
    d.text(50,995,'音频输出链路',26,ORANGE,True)
    d.text(50,1040,'板级模拟电路',20,ORANGE)
    d.card(280,954,370,148,'PT8211-S DAC  §4.2',
           ['接收 16 位 LSBJ 串行音频','数字 PCM → 模拟音频','DAC 线路输出送功放输入'],ORANGE)
    d.card(720,954,370,148,'NS4263 功放  §4.3',
           ['模拟音频功率放大','PA_EN = 0 开启 / 1 关闭','FPGA 复位期间关闭功放'],ORANGE)
    d.card(1160,954,370,148,'扬声器与听音输出  §4.4',
           ['功放 → 无源扬声器','板载听音接口 / 实际声音','采集音频，独立核验新版 L6'],ORANGE)
    d.arrow([(605,810),(605,900),(465,900),(465,954)],ORANGE)
    d.arrow([(650,1030),(720,1030)],ORANGE)
    d.arrow([(1090,1030),(1160,1030)],ORANGE)
    d.text(280,1108,'模拟输出层独立于 FPGA 逻辑；本图是功能架构，具体引脚、电平和接线见硬件拓扑。',18,ORANGE)
    d.text(40,1149,'独立候选未接入主链：延迟 / 面板、T057 曲谱上传、T058 PCM 波形；T059 BLE / 安卓仍为计划。',20)
    d.text(40,1178,'SOURCE_MODE=1 固定音 / DIAG 是诊断分支；USB MIDI 采集不代表 FPGA 已实现 USB 主机。',17)
    d.save('系统架构总图-20261007')

    d=Diagram('138K L｜音视频候选的实际结构',
              'L_locations_guard065 冻结源 / V0197 精确适配工程 · 主线 develop / 3c14bb4 · 无新版上板结论')
    d.box(30,126,1540,127,'#f4effa','#b89acd')
    d.text(50,140,'时钟与复位',25,PURPLE,True)
    d.text(280,140,'板上 50 MHz → TMDS_PLL → core 40 MHz / pixel 25 MHz / serial 125 MHz',23)
    d.text(280,181,'sys_rst_n && PLL lock → 各域复位处理；失锁关闭功放，不能照搬 60K 单域说明。',21)
    d.text(280,219,'IP 文件名 TMDS_PLL_800_600_60.v 不代表当前画面分辨率；扫描实际为 640 × 480。',19)
    d.text(40,270,'音频与事件域 · 40 MHz',26,GREEN,True)
    for x,t,lines in [(40,'输入与公共 FIFO',['按键 / MIDI 解析','双源轮转 → 32 项 FIFO','成功握手 = accepted event']), (430,'路由 / 控制快照',['router + allocator + CC64','performance_control_snapshot','锁 req_id / 槽身份 / 控制值']), (820,'FCW → 四槽 V1',['pitch_mod_snapshot_pipeline','pitch_mod_fcw_pipeline','修正 FCW → DDS / ADSR']), (1210,'PCM / LSBJ 输出',['Q15 增益 / 混音 / req_id','帧缓存 → i2s_tx → PT8211','48 kHz；同声部送 L / R'])]:
        d.card(x,315,350,164,t,lines,GREEN)
    for x in [390,780,1170]:d.arrow([(x,392),(x+40,392)],GREEN)
    d.text(50,504,'显示只旁观成功握手的事件；显示队列溢出不要求音频等待。音频采样由输出帧反向请求。',22)
    d.arrow([(215,479),(215,491),(20,491),(20,683),(40,683)],PURPLE)
    d.text(40,539,'视频支路 · CDC → 25 MHz 像素域 → 125 MHz 串行域',26,PURPLE,True)
    for x,t,lines in [(40,'事件副本跨域',['visual_event_bridge','32 项队列 / 握手邮箱','drop / desync 独立观测']), (430,'键态 / 曲谱 / 命中',['m3_visualizer','live_state / score_tracker','scene_renderer / hit_flash']), (820,'扫描与像素对齐',['video_scan_timing','640 × 480 有效区','RGB + HS/VS/DE 同拍寄存']), (1210,'DVI / TMDS 输出',['DVI_TX_Top 厂商 IP','RGB 编码 / 差分输出','HDMI 口接显示器'])]:
        d.card(x,600,350,164,t,lines,PURPLE)
    for x in [390,780,1170]:d.arrow([(x,683),(x+40,683)],PURPLE)
    d.arrow([(995,600),(995,591),(605,591),(605,600)],PURPLE)
    d.text(800,567,'扫描坐标 / 帧节拍送场景',17,PURPLE)
    d.card(40,822,640,139,'另一路显示控制', ['audio_visual_display_probe 内部诊断曲谱 / 自动模式切换', '→ visual_control_bridge / visual_mailbox_cdc → 场景'],PURPLE)
    d.arrow([(605,822),(605,764)],PURPLE)
    d.card(720,822,840,139,'诊断曲谱不是 PC 上传曲谱', ['冻结 L 使用内部生成的显示曲谱，未接 T057 的双银行读端。', '当前显示接收演奏事件；真实 PCM 波形 T058 仍在独立候选。'],ORANGE,'#fff8ee')
    d.box(30,991,1540,155,'#fff8ee','#dfba8e')
    d.text(50,1007,'集成边界与证据',25,ORANGE,True)
    d.text(50,1050,'冻结 L 未包含：动态 V1/三角切换、延迟、面板候选、T057 上传、T058 真实波形、T059 BLE。',22)
    d.text(50,1092,'V0197 的 L5 只覆盖该精确输入集合；追加任何模块后，须重新验证功能、CDC、资源和整机时序。',21)
    d.text(40,1170,'本图为源码结构审阅；实物 Bank 电压、MIDI 电平 / 共地及 HDMI 条件见原验收清单。',18)
    d.save('138K音视频候选架构-20261007')


if __name__ == '__main__':
    main()
