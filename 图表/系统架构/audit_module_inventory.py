"""Read-only source/manifest inventory. Generates the accompanying audit report."""
from pathlib import Path
import hashlib
import re
import subprocess
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
DOC = HERE.parents[1]
REPO = DOC.parent / 'fpga-electronic-piano'
LROOT = 'code/rtl/138K_try/hold_trials_20261005/L_locations_guard065'

# File role, documentation chapter. Names shared by different source trees are
# mapped separately in the output; a basename match is not byte equivalence.
ROLES = {
 'electronic_piano_top.sv':('3.1.3','60K 正式顶层；默认四声部动态双音色，SOURCE_MODE=1 为诊断分支'),
 'audio_visual_coexistence_top.sv':('3.1.3 / 3.8','138K 冻结 L 顶层；连接音频、事件显示支路与 PLL'),
 'audio_defs_pkg.sv':('3.3.1','64 位事件类型、PCM/采样率等公共常量；定义包，不是电路实例'),
 'reset_sync.sv':('3.1.1','低有效异步进入 / 目标时钟域同步解除复位'),
 'button_debouncer.sv':('3.2.1','外部按键同步、稳定时间去抖、按下/松开脉冲'),
 'button_event_converter.sv':('3.3.2 / 3.3.4','按键边沿转换为统一事件，含本地缓存'),
 'performance_event_fifo.sv':('3.3.4','双输入轮转仲裁和公共 32 项 FIFO，输出水位'),
 'system_status_counters.sv':('3.7.1','汇总输入溢出，测请求至实际提交的最大周期数'),
 'uart_status_reporter.sv':('3.7.1','锁存并格式化 STAT / DIAG 文本，调用 UART TX'),
 'uart_tx.sv':('3.7.1','字节转 UART 串行发送'),
 'uart_rx.sv':('3.2.2','异步串行同步/采样/帧检查，输出字节'),
 'midi_event_parser.sv':('3.2.2 / 3.3.3','MIDI 状态/数据字节解码、运行状态、事件缓存和连续控制调度'),
 'midi_input.sv':('3.2.2','将 UART RX 与 MIDI parser 封装为统一演奏事件输入'),
 'note_pitch.sv':('3.4.2','MIDI 音符编号映射为 48 kHz 下的基础 FCW'),
 'simple_voice.sv':('3.7.3','旧单声部诊断支路；默认四声部路径不调用'),
 'i2s_tx.sv':('3.6.2','分数分频、PCM24 转 16 位 LSBJ、双声道发送和 frame_tick'),
 'pcm_frame_buffer.sv':('3.6.1','逐帧请求/代次校验/待播与当前样本、欠载计数'),
 'voice_allocator_4.sv':('3.4.1','四槽分配和释放目标选择；由 router 接入身份与延音合同'),
 'dds_oscillator.sv':('3.4.3','基础正弦 DDS 与同文件 sine_wavetable_1024；参数分支/回归用途'),
 'piano_dds_oscillator.sv':('3.4.3','V1 钢琴 DDS 与同文件 piano_band_wavetable_1024，按音区选表'),
 'timbre_oscillator.sv':('3.5.3','正弦/三角振荡器；60K 组合中固定选择三角支路'),
 'piano_triangle_voice.sv':('3.4.3 / 3.5.3','每槽组合 V1 和三角振荡器，钢琴延迟三寄存级、三角有效时保持，按槽音色选输出'),
 'adsr_piano_envelope.sv':('3.4.4','带力度映射的 ADSR 包络状态机，按 lane_tick 推进'),
 'sustain_control_contract_pkg.sv':('3.3.3','延音命令、身份与代次合同定义包'),
 'sustain_controller.sv':('3.3.3','CC64 延迟 NoteOff、抬踏释放、panic 与声部生命周期管理'),
 'polyphonic_event_router.sv':('3.3.3 / 3.4.1 / 3.5.3','串行派发事件至 allocator/延音控制，保存声部身份；60K 版本另保存 Program/槽音色'),
 'polyphonic_envelope_bank.sv':('3.4.3 / 3.4.4 / 3.4.5','四槽波形/包络计算与结果快照；60K 含双音色，L 副本含控制快照/FCW流水线'),
 'voice_gain_q15_candidate.sv':('3.5.1','正式已例化的 Q15 波形×包络增益；candidate 文件名不等于未接入'),
 'polyphonic_pcm_commit.sv':('3.6.1','封装混音、结果保持、帧缓存和按实际提交统计削波'),
 'polyphonic_audio_core.sv':('3.1.3','封装四槽声部计算组、每槽增益、PCM提交和处理耗时；左右使用同一组 voices'),
 'pcm_mixer_4voice.sv':('3.5.1','左右各四路 PCM24 宽位累加、饱和和削波标志'),
 'pcm_clip_counter.sv':('3.5.1 / 3.7.1','仅对实际接受的削波 PCM 结果计数'),
 'pcm_result_hold.sv':('3.6.1','保持样本/req_id/clip 至握手，取消过期结果'),
 'TMDS_PLL_800_600_60.v':('3.1.1 / 3.8','TMDS_PLL IP；L 副本产生 core40/pixel25/serial125 MHz，文件名不代表扫描分辨率'),
 'DVI_TX_Top.v':('3.8','厂商 DVI/TMDS 发送 IP；文件可能含多个内部模块，不按文件数统计实例数'),
 'visual_event_bridge.sv':('3.8','已接受事件的显示队列与跨域交接，不反压音频'),
 'video_scan_timing.sv':('3.8','640×480 有效像素、同步信号与帧/行起始标志'),
 'visual_mailbox_cdc.sv':('3.8','稳定多位载荷与握手同步的邮箱原语'),
 'visual_control_bridge.sv':('3.8','显示模式和曲谱命令跨域，各用邮箱交接'),
 'visual_live_state.sv':('3.8','维护已接受演奏事件对应的键态与实时条目'),
 'visual_score_tracker.sv':('3.8','维护待命中曲谱条目、时点与持续帧数'),
 'visual_scene_renderer.sv':('3.8','把键态/曲谱状态和像素坐标转为场景颜色'),
 'visual_hit_flash.sv':('3.8','命中条件检测与闪光生命周期'),
 'm3_visualizer.sv':('3.8','组合实时状态、曲谱、场景与闪光，输出 RGB'),
 'audio_visual_display_probe.sv':('3.8','组合 PLL/桥/扫描/画面/DVI；内部生成诊断曲谱和自动模式切换'),
 'performance_control_snapshot.sv':('3.4.5','按来源/通道保存 Pitch/Mod/范围，并按请求锁存四槽一致快照'),
 'pitch_mod_fcw_pipeline.sv':('3.4.5','单槽定点弯音/颤音数学流水线，输出修正 FCW'),
 'pitch_mod_snapshot_pipeline.sv':('3.4.5','四槽带请求身份的 FCW 运算交接，保存/核对槽代次'),
}


def git(*args):
    return subprocess.check_output(['git','-c',f'safe.directory={REPO.as_posix()}','-C',str(REPO),*args],text=True).strip()


def main():
    sha=git('rev-parse','HEAD')
    assert sha.startswith('3c14bb4'), 'Update the human audit before changing the evidence baseline.'
    doc=(DOC/'系统模块总览.md').read_text(encoding='utf8')
    out=['# 系统模块与代码工程对应核查', '',f'核查日期：2026-10-07；源码 `develop / {sha}`。',
         '', '证据级别：L0 静态审阅。已 fetch，当前 HEAD 与 origin/develop 一致；没有重新仿真、综合或上板。',
         '', '## 结论与范围', '',
         '38 个详细设计章节是功能分组，包含软件、硬件、候选及计划，不是 38 个已接入的 HDL 模块。32 个 60K 工程 HDL 文件和 45 个冻结 L 工程 HDL 文件均已逐文件归类；文件数包含包、IP 和参数分支，不等于综合后的实例数。',
         '', '以工程 FileList、顶层例化、generate 参数和实际信号连接共同判定集成；同名副本不能互相替代。未把 `tb/` 候选、`pop_repair/` 研究、`138K_try/` 历史试验目录当作当前正式模块。',
         '', '## 38 个功能章节的对应关系', '', '| 章节 | 类型 / 集成边界 | 代表文件或依据 |', '|---|---|---|']
    overrides={
      '2.7':('跨软件/RTL独立候选；未接入两顶层','code/rtl/input/score_transfer_candidate/score_transfer_candidate.sv'),
      '2.8':('计划；当前未交付 BLE 固件/App','code/docs/M3_扩展工作边界与阶段交付_2026-10-07.md'),
      '3.1.2':('正式帧调度；独立sample_tick_gen未入工程','code/rtl/audio_out/pcm_frame_buffer.sv'),
      '3.3.1':('公共数据合同，不是独立电路实例','code/rtl/common/audio_defs_pkg.sv'),
      '3.3.5':('面板隔离候选；未接入两顶层','code/tb/board/panel_verified_control_candidate/panel_score_transport.sv'),
      '3.4.5':('60K力度/延音已接；Pitch/Mod接入冻结L候选',LROOT+'/sources/pitch_mod_snapshot_pipeline.sv'),
      '3.5.2':('独立延迟候选；未接入两顶层','code/rtl/audio/delay_effect.sv'),
      '3.5.3':('60K正式双音色；冻结L没有动态切换','code/rtl/board/piano_triangle_voice.sv'),
      '3.7.2':('独立探针工程；非正式顶层模块','code/rtl/board/uart_echo_probe.sv'),
      '3.7.3':('参考模型/待返修离线候选；未接正式工程','code/model/generate_test_mode_reference.py'),
      '3.8':('冻结L候选已接事件显示；60K正式工程未接',LROOT+'/sources/audio_visual_display_probe.sv'),
      '3.9':('观察/CDC独立候选；像素绘图和整机接入待交付','code/rtl/common/pcm_waveform_observer_candidate/pcm_waveform_observer_bridge.sv'),
    }
    count=0
    for m in re.finditer(r'^#{3,4} (\d[^\n]+)\n([\s\S]*?)(?=^#{1,4} |\Z)',doc,re.M):
        if '##### 1.' not in m[2]:continue
        title=m[1];key=title.split(' ')[0];count+=1
        paths=re.findall(r'`(code/[^`]+\.(?:sv|py|ps1|cst|gprj))`',m[2])
        path=paths[0] if paths else 'code/docs/板级硬件事实.md'
        kind='开发/观测软件，不承担FPGA实时合成' if key.startswith('2.') else ('外部/板载硬件；无独立RTL模块' if key.startswith('4.') else '正式音频链路功能分组')
        kind,path=overrides.get(key,(kind,path))
        assert (REPO/path).is_file(),path
        out.append(f'| {title} | {kind} | [{Path(path).name}](../../../fpga-electronic-piano/{path}) |')
    assert count==38,count
    out+=['','## 工程文件逐项归属','','下列链接指向核查时的本地源码。复核时应先确认上方提交号；原工程中的绝对路径仅按 `fpga-electronic-piano/` 后缀映射到本机用于阅读，没有修改工程。']
    for label,proj in [('60K 正式工程','code/build/electronic_piano.gprj'),('138K 冻结 L 候选',LROOT+'/audio_visual_coexistence_top.gprj')]:
        p=REPO/proj;files=[]
        for e in ET.parse(p).findall('.//File'):
            if e.get('type')!='file.verilog' or e.get('enable')!='1':continue
            raw=e.get('path')
            f=(p.parent/raw).resolve() if ':' not in raw else REPO/raw.split('fpga-electronic-piano/',1)[1]
            assert f.is_file(),f
            files.append(f)
        out+=['',f'### {label}：{len(files)} 个启用的 HDL 文件','',f'入口：[{proj}](../../../fpga-electronic-piano/{proj})','',
              '| 文件 | 章节 | 作用 / 生效边界 | SHA-256（前12位） |','|---|---|---|---|']
        for f in files:
            chapter,role=ROLES[f.name]
            path=f.relative_to(REPO).as_posix()
            out.append(f'| [{f.name}](../../../fpga-electronic-piano/{path}) | {chapter} | {role} | `{hashlib.sha256(f.read_bytes()).hexdigest()[:12]}` |')
    out+=['','## 其他源码的归类','','- `sample_tick_gen.sv`：独立节拍发生器与回归；正式声音由 i2s_tx 帧边界请求，不是双时基并行驱动。',
      '- `voice_gain_q15_candidate.sv`：虽有 candidate 后缀，已由两工程的音频核心实际例化。',
      '- `dds_oscillator.sv`：在两个工程清单中，但默认钢琴/双音色配置走其他 generate 分支；不要将基础正弦同时画作默认音色。',
      '- `piano_dds_oscillator.sv` / `dds_oscillator.sv` 内各有波表存储子模块；`.mem/.hex/.svh` 是 ROM、常量或合同依赖，不应漏带，也不按独立功能章节计数。',
      '- `adsr_scale_probe.sv`、`polyphonic_envelope_bank_probe.sv`、`voice_datapath_probe.sv`：算法/声部计算组/数据通路独立资源或行为探针，归入第2.5节构建验证工具。',
      '- `visual_cdc_probe.sv`、`visual_control_probe.sv`、`visual_full_path_probe.sv`、`visual_resource_probe.sv`：显示跨域/控制/全路径/资源独立探针，归入第3.8节验证工具。',
      '- `code/tb/` 含面板、Pitch/Mod、深流水等隔离可综合候选；有RTL文件不代表已被正式工程引用。',
      '- `code/rtl/pop_repair/` 的V2/V3及 `138K_try/` 非L试验/恢复目录为研究和追溯材料，不能与当前V1或精确L输入混装。',
      '', '## 已修正文档与框图的问题', '',
      '| 原问题 | 修正 |', '|---|---|',
      '| 9月19日旧图仍写 MIDI待接入、完整多声部待集成 | 以当前正式输入、四槽DDS/ADSR、CC64、动态音色、逐帧交付和STAT重绘 |',
      '| 60K和138K的功能/时钟被同一“当前系统”概括 | 分开正式60K总图与138K冻结L候选图，列出双音色/Pitch-Mod/HDMI差异 |',
      '| 缺失正式每槽波形组合文件 | 第3.4.3/3.5.3补充piano_triangle_voice的延迟对齐、保持和选择作用 |',
      '| 容易把抽象功能/独立发生器/探针当作已实例化模块 | 保留38个功能章节，增加逐章节类型和全部工程文件对应表 |',
      '| 显示曲谱可能被理解为上传后自动播放 | 写明冻结L内部诊断曲谱，T057读端尚未接到播放/显示 |',
      '| 线性总图缺少时基反向请求与状态回传 | 增加frame_tick→sample_req/req_id和UART STAT观测路径 |',
      '| 双声道可能被误认为独立立体声合成 | 标明当前core同一voices连接左右混音输入；接口有左右不等于独立声像 |',
      '', '## 源码侧建议（仅监督，未修改）', '',
      'M2后续可清理 `electronic_piano_top.sv` 头部“Pitch/Mod/Sustain效果仍待实现”和早期测试音步长说明，以及L顶层遗留单50MHz域说明；实际例化/公式已与这些旧注释不同。验收应以默认参数展开的通路和新报告为准。',
      '', '138K 若要合并60K双音色及新的曲谱/波形候选，需由M2制定精确输入清单与整机复核；M1确认音色/定标，M3提供像素模块和实体接口证据。当前审阅不授权修改源码或下载。',
      '', '复现：运行同目录 `audit_module_inventory.py`；图件由 `generate_architecture.py` 生成。生成器只读取源码并写入本地文档仓库。']
    # Audit lives two levels beneath the document root.
    # ../../../fpga-electronic-piano is the sibling repo from this directory.
    (HERE/'模块与工程对应核查.md').write_text('\n'.join(out)+'\n',encoding='utf8',newline='\n')
    print(f'Checked {count} functional sections, 32 + 45 project HDL entries.')


if __name__=='__main__':main()
