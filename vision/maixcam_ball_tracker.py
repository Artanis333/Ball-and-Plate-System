"""
MaixCam 白色小球识别与串口坐标回传程序
功能：在黑色背景下识别纯白色小球，并通过串口回传xy坐标
波特率：115200
"""

from maix import camera, display, image, uart, pinmap, time, app, err, sys
from struct import pack

# ============== 配置参数 ==============
# 串口配置 - 根据设备ID自动选择
device_id = sys.device_id()
if device_id == "maixcam2":
    pin_function = {
        "A21": "UART4_TX",
        "A22": "UART4_RX"
    }
    device = "/dev/ttyS4"
else:
    pin_function = {
        "A16": "UART0_TX",
        "A17": "UART0_RX"
    }
    device = "/dev/ttyS0"

# 设置引脚功能
for pin, func in pin_function.items():
    err.check_raise(pinmap.set_pin_function(pin, func), f"Failed set pin{pin} function to {func}")

# 颜色阈值配置 (LAB色彩空间)
# 白色在LAB空间中的阈值范围: L高(亮度高), A和B接近0(无色偏)
# 格式: [L_min, L_max, A_min, A_max, B_min, B_max]
thresholds = [[70, 100, -30, 30, -30, 30]]   # 白色阈值

# 小球检测参数 - 针对14mm小球优化
area_threshold = 100       # 最小面积阈值，过滤小噪点
pixels_threshold = 100     # 最小像素数阈值
max_area = 2000           # 最大面积阈值

# 面积范围（用于评分，14mm小球在256x256分辨率下的预期面积范围）
expected_min_area = 100    # 预期最小面积
expected_max_area = 1200  # 预期最大面积

# ============== 初始化 ==============
# 初始化摄像头 - 使用正方形分辨率256x256
# 这样X和Y坐标都在0-255范围内，适合单字节传输
cam = camera.Camera(256, 256)

# 初始化显示
disp = display.Display()

# 初始化串口
serial_dev = uart.UART(device, 115200)

print("白色小球识别程序已启动...")
print(f"设备ID: {device_id}")
print(f"串口: {device}, 波特率: 115200")
print("按 Ctrl+C 或点击退出按钮停止程序")

# 发送启动消息
serial_dev.write_str("Ball Tracker Started\r\n")


def calculate_ball_score(blob):
    """
    计算blob作为小球的评分
    评分考虑: 圆形度、密度、面积适中程度、宽高比
    返回: 评分(0-100), 数值越高越像小球
    """
    score = 0
    
    # 1. 圆形度评分 (0-40分)
    roundness = blob.roundness()
    score += roundness * 40  # roundness范围0-1
    
    # 2. 密度评分 (0-20分)
    density = blob.density()
    score += density * 20
    
    # 3. 面积适中程度评分 (0-20分)
    area = blob.area()
    if expected_min_area <= area <= expected_max_area:
        # 在预期范围内得满分
        score += 20
    elif area < expected_min_area:
        # 太小，按比例扣分
        score += 20 * (area / expected_min_area)
    else:
        # 太大，按比例扣分
        score += 20 * (expected_max_area / area)
    
    # 4. 宽高比评分 (0-20分)
    w = blob.w()
    h = blob.h()
    if h > 0 and w > 0:
        aspect_ratio = min(w, h) / max(w, h)  # 越接近1越好
        score += aspect_ratio * 20
    
    return score


# ============== 主循环 ==============
last_send_time = time.time_ms()
SEND_INTERVAL = 50  # 串口发送间隔(毫秒)

while not app.need_exit():
    # 获取摄像头图像
    img = cam.read()
    
    if img is None:
        print("无法读取摄像头图像")
        time.sleep_ms(10)
        continue
    
    # 在LAB空间中检测白色区域
    blobs = img.find_blobs(thresholds, area_threshold=area_threshold, pixels_threshold=pixels_threshold)
    
    # 存储检测到的小球坐标
    ball_x = -1
    ball_y = -1
    ball_found = False
    
    if blobs:
        # 过滤面积过大的blob
        candidate_blobs = [b for b in blobs if b.area() <= max_area]
        
        if candidate_blobs:
            # 使用评分机制选择最像小球的blob
            best_blob = max(candidate_blobs, key=calculate_ball_score)
            best_score = calculate_ball_score(best_blob)
            
            # 只接受评分超过阈值的blob
            if best_score >= 30:  # 评分阈值
                ball_found = True
                ball_x = best_blob.cx()
                ball_y = best_blob.cy()
                
                # 在图像上绘制标记
                rect = best_blob.rect()
                
                # 绘制边界框
                corners = best_blob.corners()
                for i in range(4):
                    img.draw_line(corners[i][0], corners[i][1], 
                                  corners[(i + 1) % 4][0], corners[(i + 1) % 4][1], 
                                  image.COLOR_GREEN, 2)
                
                # 绘制中心十字线
                img.draw_cross(ball_x, ball_y, image.COLOR_RED, size=10, thickness=2)
                
                # 绘制外接圆
                enclosing_circle = best_blob.enclosing_circle()
                img.draw_circle(enclosing_circle[0], enclosing_circle[1], 
                               int(enclosing_circle[2]), image.COLOR_BLUE)
                
                # 显示坐标文本
                text = f"({ball_x}, {ball_y})"
                img.draw_string(rect[0], rect[1] - 15, text, image.COLOR_WHITE)
                
                # 显示调试信息
                img.draw_string(rect[0], rect[1] + rect[3] + 5, 
                               f"A:{best_blob.area()} S:{best_score:.0f}", 
                               image.COLOR_WHITE)
    
    # 显示处理后的图像
    disp.show(img)
    
    # 定时发送串口数据
    current_time = time.time_ms()
    if current_time - last_send_time >= SEND_INTERVAL:
        # 发送三字节二进制数据: [帧头, X, Y]
        # 帧头: 检测到小球为0x55，未检测到为0x50
        # X, Y: 坐标范围0-255
        if ball_found:
            header = 0x55  # 检测到小球
            x_byte = ball_x if ball_x <= 255 else 255
            y_byte = ball_y if ball_y <= 255 else 255
        else:
            header = 0x50  # 未检测到小球
            x_byte = 0
            y_byte = 0
        
        data = bytes([header, x_byte, y_byte])
        serial_dev.write(data)
        last_send_time = current_time
        print(f"发送: [0x{header:02X}, {x_byte}, {y_byte}]")

# 程序退出
serial_dev.write_str("Ball Tracker Stopped\r\n")
print("程序退出")