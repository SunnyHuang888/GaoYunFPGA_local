# FPGA 入门概要

更新时间：2026-09-19  
适用对象：第一次接触 FPGA、SystemVerilog 和 Gowin EDA 的初学者  
项目背景：Tang Mega 60K + NEO Dock 实时音频电子琴

## 1. FPGA 到底是什么

FPGA 是一块可以反复配置的数字电路芯片。它不是像电脑那样运行一个程序，而是根据配置数据搭建出一组硬件电路。

可以先记住这条链路：

```text
SystemVerilog 硬件描述
    -> 综合
    -> 布局布线
    -> 时序分析
    -> 生成 FPGA 码流
    -> 下载到 FPGA
    -> 硬件电路运行
```

FPGA 适合做并行、实时、固定时序的任务，例如：

- 音频采样和实时合成
- 电机控制
- 图像和视频处理
- 高速通信
- 自定义外设和接口

## 2. 三个最容易混淆的概念

### 2.1 HDL

HDL 是硬件描述语言的统称，英文是 Hardware Description Language。

Verilog、SystemVerilog 和 VHDL 都属于 HDL。

### 2.2 SystemVerilog

SystemVerilog 是一种具体的 HDL，是 Verilog 的增强版。它支持：

- `logic`
- `always_ff`、`always_comb`
- `struct`、`enum`、`package`
- 参数化模块
- 断言和 Testbench

### 2.3 `.sv`

`.sv` 是 SystemVerilog 文件扩展名，不是另一种语言。

```text
reset_sync.sv
    文件名
SystemVerilog
    使用的语言
HDL
    所属类别
```

常见文件：

| 扩展名 | 用途 |
|---|---|
| `.sv` | SystemVerilog |
| `.v` | Verilog |
| `.vhd`、`.vhdl` | VHDL |
| `.cst` | Gowin 引脚和 IO 约束 |
| `.sdc` | 时钟和时序约束 |
| `.fs` | Gowin FPGA 配置码流 |
| `.vcd` | 仿真波形 |

## 3. 软件思维和 FPGA 思维

软件通常是：

```text
CPU 取一条指令 -> 执行 -> 再取下一条指令
```

FPGA 更接近：

```text
多个硬件模块同时工作
寄存器在时钟沿更新
组合逻辑在寄存器之间计算
```

下面的代码不是“循环执行 10 次”，而是描述 10 个寄存器和一组加法逻辑：

```systemverilog
always_ff @(posedge clk) begin
    if (!rst_n)
        counter <= 0;
    else
        counter <= counter + 1;
end
```

这段代码表示：

- `counter` 是寄存器
- `posedge clk` 是寄存器更新时刻
- `counter + 1` 是组合加法器
- `rst_n` 是低有效复位

初学者最重要的习惯是：看到代码时问“它会变成什么硬件”，而不只是问“它按什么顺序执行”。

## 4. 一个 FPGA 工程由什么组成

本项目的主要目录如下：

| 目录 | 内容 |
|---|---|
| `rtl/` | 正式可综合的 SystemVerilog 硬件模块 |
| `tb/` | Testbench，只用于仿真验证 |
| `constraints/` | `.cst` 引脚约束和 `.sdc` 时序约束 |
| `model/` | Python 黄金模型和数值参考 |
| `scripts/` | 仿真、检查、构建和下载脚本 |
| `docs/` | 接口、设计决策、任务和验证记录 |
| `build/` | Gowin 工程和生成的构建结果 |

当前正式工程入口是 `fpga-electronic-piano/code/README.md`。

## 5. 从 RTL 到上板的流程

### 5.1 综合

综合把 SystemVerilog 转换成 FPGA 资源：

| RTL 内容 | 常见 FPGA 资源 |
|---|---|
| 寄存器 | FF |
| 加法、比较、选择 | LUT / ALU |
| 大数组、FIFO | BSRAM |
| 乘法 | DSP 或 LUT |
| 顶层端口 | IO 资源 |

综合主要检查：

- 语法和模块连接是否正确
- 代码是否可综合
- 需要多少 LUT、FF、BSRAM、DSP

### 5.2 布局布线

布局决定每个逻辑资源放在 FPGA 的哪里，布线决定它们通过哪些内部连线连接。

布局布线还会处理外部引脚。例如本项目的音频接口：

```text
sys_clk   -> V22
I2S_BCLK  -> Y17
i2s_lrck  -> AB17
i2s_din   -> AA16
pa_en     -> AB16
```

布局布线主要检查：

- 资源是否足够
- 引脚是否冲突
- IO 电气标准是否正确
- 专用时钟和专用引脚是否被正确使用
- 内部连线是否能够完成

### 5.3 时序分析

时序分析检查数据能否在规定时间内稳定到达。

本项目使用：

```text
sys_clk = 50 MHz
时钟周期 = 20 ns
sample_tick = 48 kHz
I2S BCLK = 3.072 MHz
```

重点指标：

| 指标 | 含义 | 通常目标 |
|---|---|---|
| Setup | 数据是否到达太晚 | 无违例 |
| Hold | 数据是否变化太早 | 无违例 |
| Slack | 时序余量 | 大于等于 0 |
| WNS | 最差路径余量 | 大于等于 0 |
| TNS | 所有违例总和 | 等于 0 |
| Fmax | 理论最高频率 | 高于目标频率 |

仿真通过不代表时序通过。仿真验证逻辑行为，时序分析验证电路速度。

`Fmax` 是工具根据当前 RTL、约束和布局布线结果估算的关键路径上限，不是 FPGA 芯片固定不变的最高频率。改动逻辑、约束或布局后，报告中的 `Fmax` 都可能变化。

### 5.4 FPGA 码流

Gowin 生成的 `.fs` 文件是 FPGA 配置码流，不是普通软件程序。

它包含：

- LUT 的配置
- 触发器和内部连线配置
- BSRAM 初始内容
- IO 引脚配置
- 时钟资源配置
- 电气标准和上下拉配置

下载码流后，FPGA 才会按照设计搭建出硬件电路。

## 6. 时钟、复位和采样节拍

这是 FPGA 初学者最应该先学会的基础。

### 6.1 时钟

时钟是所有时序逻辑更新的基准。当前项目只有一个主要内部时钟 `sys_clk`，来自开发板 50 MHz 晶振。

不要随意用普通逻辑生成新时钟。通常应使用：

```systemverilog
always_ff @(posedge sys_clk) begin
    if (enable)
        state <= next_state;
end
```

这里 `enable` 是时钟使能，而不是新的时钟。

### 6.2 复位

本项目采用低有效复位，允许异步拉低、在目标时钟域同步释放。当前工程的实际命名是：

- 顶层外部输入：`sys_rst_n`
- 复位同步器输出：`rst_sync_n`

对应代码：

- `code/rtl/common/reset_sync.sv`
- `code/rtl/board/electronic_piano_top.sv` 中的 `u_reset_sync`

### 6.3 `sample_tick`

`sample_tick` 是 48 kHz 的单周期时钟使能，不是独立时钟：

```systemverilog
always_ff @(posedge sys_clk) begin
    if (!sys_rst_n)
        phase <= '0;
    else if (sample_tick)
        phase <= phase + phase_step;
end
```

对应代码：

- `code/rtl/common/sample_tick_gen.sv`
- `code/rtl/common/audio_defs_pkg.sv`
- `code/rtl/board/electronic_piano_top.sv`

## 7. 当前项目的音频数据流

```text
按键或 MIDI
    -> 输入适配
    -> 统一演奏事件 performance_event_t
    -> 事件 FIFO
    -> 声部管理
    -> 音高查表 / FCW
    -> DDS 波表
    -> ADSR
    -> 混音和饱和限幅
    -> 24 位 PCM
    -> I2S 发送
    -> PT8211 DAC
    -> NS4263 功放
    -> 耳机或扬声器
```

当前冻结的关键接口：

| 接口 | 规格 |
|---|---|
| `performance_event_t` | 64 位 |
| 事件 FIFO | 深度 32，valid-ready 反压 |
| `sample_tick` | 48 kHz，单个 `sys_clk` 周期脉冲 |
| PCM | 24 位有符号补码 |
| I2S | 48 kHz、64 BCLK/帧、3.072 MHz BCLK |
| DAC 有效数据 | 16 位，LSBJ 右对齐，MSB first |
| 复位 | 低有效，异步拉低、同步释放 |

完整接口以 `fpga-electronic-piano/code/docs/模块接口规范.md` v1.2 为准。

## 8. 初学者推荐上手顺序

### 第一步：先看最小硬件模块

建议按这个顺序阅读：

1. `code/rtl/common/reset_sync.sv`
2. `code/rtl/common/sample_tick_gen.sv`
3. `code/tb/common/tb_reset_sync.sv`
4. `code/tb/common/tb_sample_tick_gen.sv`
5. `code/rtl/board/electronic_piano_top.sv`

先理解一个寄存器、一个复位同步器和一个节拍脉冲，比一开始阅读完整音频系统更有效。

### 第二步：运行 T019 时钟复位仿真

在 PowerShell 中先进入正式工程根目录再执行：

```powershell
Set-Location .\fpga-electronic-piano
. .\code\scripts\enter_fpga_env.ps1
.\code\scripts\run_t019_sim.ps1
```

预期结果：三个 Testbench 通过，输出 PASS，退出码为 0。

### 第三步：理解一个输入到输出的闭环

继续阅读：

- `code/rtl/input/button_debouncer/button_debouncer.sv`
- `code/rtl/input/button_event_converter/button_event_converter.sv`
- `code/rtl/common/note_pitch.sv`
- `code/rtl/common/simple_voice.sv`
- `code/rtl/audio_out/i2s_tx.sv`

### 第四步：运行项目检查

```powershell
.\code\scripts\check_fpga_env.ps1
.\code\scripts\check_repo.ps1
```

`check_repo.ps1` 主要检查静态结构、脚本、引脚一致性和已有回归；它不等价于完整综合或上板验收。

### 第五步：再尝试 Gowin 构建和下载

正式构建前确认：

- 顶层模块正确
- `.cst` 引脚和顶层端口一致
- `.sdc` 创建了正确的时钟约束
- 复位和时钟已经验证
- 仿真已经 PASS
- 下载工具、USB 线和开发板供电正常

## 9. 仿真、综合、上板分别证明什么

| 阶段 | 能证明什么 | 不能证明什么 |
|---|---|---|
| Python 模型 | 数学算法和参考结果 | RTL 语法、FPGA 时序 |
| RTL 仿真 | 逻辑行为和边界条件 | 真实资源、引脚、电气和上板声音 |
| 综合 | RTL 可映射到 FPGA 资源 | 内部布线和最终时序 |
| 布局布线 | 资源和物理连接可完成 | 真实外设是否接线正确 |
| 时序分析 | 目标时钟下理论上能稳定工作 | 外部电源、接插件和模拟音质 |
| 码流下载 | FPGA 已配置 | 功能、声音和接口一定正确 |
| 上板实测 | 真实硬件链路在当前条件下工作 | 其他板卡、其他码流版本必然相同 |

报告时要明确写验证等级，不能把“仿真通过”写成“上板通过”。

本项目使用以下验证等级：

| 等级 | 含义 |
|---|---|
| L0 | 文档或静态检查完成 |
| L1 | lint 或编译通过 |
| L2 | 自检仿真 PASS |
| L3 | 与 Python 参考模型比较 PASS |
| L4 | Gowin 综合通过 |
| L5 | 布局布线完成且时序收敛 |
| L6 | 已下载到开发板并实测 |
| L7 | 整机连续运行和故障恢复通过 |

## 10. 初学者常见错误

### 10.1 把 `sample_tick` 当时钟

错误：

```systemverilog
always_ff @(posedge sample_tick)
```

正确：

```systemverilog
always_ff @(posedge sys_clk) begin
    if (sample_tick)
        sample <= next_sample;
end
```

### 10.2 忘记给时序逻辑复位

寄存器没有明确初始状态，仿真可能出现 `X`，上板可能出现不可预测行为。

### 10.3 用阻塞赋值写时序逻辑

时序逻辑通常使用：

```systemverilog
always_ff @(posedge clk)
    q <= d;
```

组合逻辑使用 `always_comb` 和阻塞赋值 `=`。

### 10.4 多位总线直接跨时钟域

单比特可以用双触发器同步，多位数据需要握手、Gray 码或异步 FIFO。

### 10.5 只看仿真，不看资源和时序

一个模块仿真正确，仍可能因为 LUT 太多、路径太长或 BRAM 不够而无法布局布线。

### 10.6 把 5 V 信号直接接到 FPGA

当前 FPGA IO 不是 5 V 容忍输入。接入 MIDI、串口或传感器前必须确认电平并共地。

### 10.7 下载时先怀疑代码，忽略供电和接触

遇到“找不到 FPGA”或“没有声音”时，按这个顺序排查：

```text
电源与开机状态
    -> USB/JTAG 连接
    -> 下载器枚举和器件扫描
    -> 码流是否真的下载成功
    -> 复位和引脚约束
    -> 协议时序
    -> 数据格式和数值
    -> 耳机、插头、功放和音量
```

## 11. 常用术语速查

| 术语 | 含义 |
|---|---|
| RTL | 寄存器传输级硬件描述 |
| LUT | 查找表逻辑单元 |
| FF | 触发器 |
| BSRAM | FPGA 内部块 RAM |
| DSP | FPGA 内部乘法和数字信号处理资源 |
| CDC | Clock Domain Crossing，跨时钟域处理 |
| DUT | Device Under Test，被测设计 |
| TB | Testbench，仿真测试平台 |
| CST | Gowin 引脚和 IO 约束文件 |
| SDC | 时钟和时序约束文件 |
| PnR | Place and Route，布局布线 |
| WNS | Worst Negative Slack，最差时序余量 |
| TNS | Total Negative Slack，总负时序余量 |
| bitstream | FPGA 配置码流 |
| SRAM 下载 | 临时下载，断电后通常丢失 |
| Flash 下载 | 固化下载，断电后可自动加载，具体方式需按板卡和工具确认 |

## 12. 推荐记住的五句话

1. SystemVerilog 描述的是硬件，不是普通软件程序。
2. `always_ff` 描述寄存器，时钟沿决定寄存器何时更新。
3. 仿真通过不等于综合、时序和上板都通过。
4. `.cst` 管引脚和 IO 电气属性，`.sdc` 管时钟和时序要求。
5. 修改后按“仿真 -> 综合 -> 布局布线与时序 -> 生成码流 -> 下载 -> 上板”逐级验证。

## 13. 相关文档

- `fpga-electronic-piano/code/README.md`：正式工程入口和常用命令
- `fpga-electronic-piano/code/docs/模块接口规范.md`：公共接口基线
- `fpga-electronic-piano/code/docs/开发环境.md`：工具和环境要求
- `fpga-electronic-piano/code/docs/板级硬件事实.md`：开发板、供电、引脚和下载排障
- `fpga-electronic-piano/code/docs/测试验收标准.md`：验证等级和验收口径
- `fpga-electronic-piano/code/docs/协作入口.md`：任务和协作入口
- `离线文档/系统模块总览.md`：系统模块、成果和接口总览
