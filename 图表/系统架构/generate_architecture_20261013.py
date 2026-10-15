from pathlib import Path
import importlib.util
D=Path(__file__).resolve().parents[2]
# Reuse the existing vector/raster diagram primitives, retaining the established 4:3 layout.
spec=importlib.util.spec_from_file_location('arch',D/'图表/系统架构/generate_architecture.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
d=m.Diagram('高云杯电子琴｜最新三层系统与独立候选','2026-10-13 · 7fd3e17 · 四声部组合L5 / 实物未验 · 独立N32综合L4 / STA未验')
for y,label,color in [(140,'第一层  上位机与辅助软件',m.BLUE),(415,'第二层  FPGA精确四声部音画 / 曲谱组合',m.GREEN),(780,'第三层  板级输出与独立扩展边界',m.ORANGE)]:
 d.box(30,y,1540,245 if y!=415 else 330,stroke=color);d.text(48,y+12,label,25,color,True)
cards=[(50,195,'开发与参考',['PC / Gowin / 仿真','T060独立数学：PARTIAL','T052 WAV：软件辅助'],m.BLUE),(430,195,'演奏输入与监视',['DIN MIDI / 板载按键','USB MIDI监视 / STAT','PC不生成正式音频'],m.BLUE),(810,195,'安卓 / ESP32-C3',['APK和固件已真实构建','BLE桥接原曲谱协议','实体无线 / ACK未验'],m.BLUE),(1190,195,'曲谱输入',['JSON → 规范事件','512事件 / CRC / READ','MIDI检索仍仅建议'],m.BLUE),
(50,475,'事件与实时合成',['仲裁 / FIFO / CC64','四声部DDS / ADSR','Pitch / Mod / PCM24'],m.GREEN),(430,475,'帧交付与发送',['请求代次 / 截止期','hold / commit / 缓存','PT8211 LSBJ输出'],m.GREEN),(810,475,'只读波形显示',['实际PCM → 队列 / CDC','min-max像素 / 快照','固定左波形，无FFT'],m.GREEN),(1190,475,'曲谱同步存储',['T062双区BSRAM','UART / CRC / 请求缓存','已接收存储，未接播放'],m.GREEN),
(50,835,'模拟音频链路',['PT8211 DAC','NS4263功放 → 扬声器','新版实体链路待验'],m.ORANGE),(430,835,'视频与硬件条件',['HDMI / DVI显示器','电平 / 供电 / 恢复核实','同版音画实屏未验'],m.ORANGE),(810,835,'T061独立候选',['N8 / N16 / N32数字验证','显式pROM实际综合L4','长路径待优化 / STA未验'],m.PURPLE),(1190,835,'旧版与非目标',['保留60K / 原138K L','两音色60K另版验证','播放 / 频谱未获接入'],m.PURPLE)]
for x,y,t,ls,col in cards:d.card(x,y,350,160,t,ls,col)
d.arrow([(605,355),(605,397),(225,397),(225,475)])
d.arrow([(985,355),(985,400),(1365,400),(1365,475)],dash=True)
d.arrow([(1365,355),(1365,475)])
d.arrow([(400,555),(430,555)],m.GREEN);d.arrow([(780,555),(810,555)],m.GREEN)
d.arrow([(605,635),(605,762),(225,762),(225,835)],m.ORANGE)
d.arrow([(985,635),(985,765),(605,765),(605,835)],m.ORANGE)
d.text(45,1038,'40MHz音频 / 25MHz像素 / 125MHz串行；V0264：Setup +1.637 ns / Hold 0 / Recovery +0.325 ns',20)
d.text(45,1072,'62输入 / 53工程项；32 BSRAM / 46 DSP；当前候选进入develop ≠ 正式启用或上板通过',20)
d.text(45,1106,'实线：数字通路；虚线：实体无线链路待验；紫色框：独立候选/历史边界，不计入四声部整机。',21)
d.text(45,1140,'曲谱上传与ACK/READ ≠ 自动播放；屏幕波形 ≠ 频谱；目标构建成功 ≠ 手机和板卡链路已验。',21)
d.save('系统架构总图-20261013')
print('Added four seven-part modules and generated 4:3 PNG/SVG architecture')
