/*
 * Copyright (c) 2021, Texas Instruments Incorporated
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * *  Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * *  Neither the name of Texas Instruments Incorporated nor the names of
 *    its contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "ti_msp_dl_config.h"
#include "main.h"
#include <math.h>
int motor_couter[2] = {0},READY_TO_GO = 0,CYCLE_FLAG = 0,CYCLE_TIME = 0,target_x =127,target_y =127;
float motor_location[2] = {0,0};
float SET0_P = 2.35,SET0_R = -1.20,tag_p = 2.35,tag_r =-1.20;
PID_LocTypeDef pid1,pid2,pid3,pid4,pid5,pid6; // 添加中环PID
float ball_vx = 0, ball_vy = 0;
// 圆轨迹参数
#define CIRCLE_CX 127  // 圆心X (图像中心)
#define CIRCLE_CY 127  // 圆心Y
#define CIRCLE_R  75   // 半径
#define LEAD_ANGLE 20  // 超前角度(度)，顺时针为正
// const float vel_filter_alpha = 0.7f; // 速度低通滤波系数，越大滤波越强  // 移除低通滤波
int last_x = 127, last_y = 127; // 假设初始中心

// 卡尔曼滤波结构体
typedef struct {
    float x;      // 状态估计值 (速度)
    float P;      // 估计误差协方差
    float Q;      // 过程噪声协方差
    float R;      // 测量噪声协方差
} KalmanFilter;

KalmanFilter kf_vx, kf_vy;

// 初始化卡尔曼滤波器
void Kalman_Init(KalmanFilter *kf, float initial_x, float P, float Q, float R) {
    kf->x = initial_x;
    kf->P = P;
    kf->Q = Q;
    kf->R = R;
}

// 卡尔曼滤波更新
float Kalman_Update(KalmanFilter *kf, float measurement) {
    // 预测
    float x_pred = kf->x;  // 假设速度恒定
    float P_pred = kf->P + kf->Q;

    // 更新
    float K = P_pred / (P_pred + kf->R);  // 卡尔曼增益
    kf->x = x_pred + K * (measurement - x_pred);
    kf->P = (1 - K) * P_pred;

    return kf->x;
}
int main(void)
{
    
    SYSCFG_DL_init();
    SysTick_Init();
    DL_TimerA_startCounter(PWM_1_INST);
    DL_TimerA_startCounter(TIMER_0_INST);
    NVIC_EnableIRQ(PWM_1_INST_INT_IRQN);
    NVIC_EnableIRQ(TIMER_0_INST_INT_IRQN);
    NVIC_EnableIRQ(GPIO_KEY_INT_IRQN);
    PID_INIT(7, 0.03, 0.001,&pid1);// 内环电机角度PID
    PID_INIT(7, 0.03, 0.001,&pid2);
    PID_INIT(1.1, 0.005, 0.3,&pid3); // 外环位置PID
    PID_INIT(1.1, 0.005, 0.3,&pid4);
    pid3.i_max = 400.0f;              // 位置环积分钳位,防止stick-slip过冲
    pid4.i_max = 400.0f;
    PID_INIT(1.2, 0.01, 0.15,&pid5); // 中环速度PID
    PID_INIT(1.2, 0.01, 0.15,&pid6);
    // MPU6050_Init();
    // OLED_Init();
    // Ultrasonic_Init();
    // BNO08X_Init();
    WIT_Init();
    MAIX_Init();

    // 初始化卡尔曼滤波器
    Kalman_Init(&kf_vx, 0.0f, 1.0f, 0.1f, 1.1f);  // 初始速度0, 协方差1, 过程噪声0.1, 测量噪声1
    Kalman_Init(&kf_vy, 0.0f, 1.0f, 0.1f, 1.1f);
    while (1) 
    {

    }
}
void PWM_1_INST_IRQHandler(void)//
{
    
    if(DL_TimerA_getEnabledInterruptStatus(PWM_1_INST,DL_TIMER_INTERRUPT_ZERO_EVENT) == DL_TIMER_INTERRUPT_ZERO_EVENT)
    {
    if(motor_couter[0]<0)
    {
    DL_TimerA_setCaptureCompareValue(PWM_1_INST, 25, GPIO_PWM_1_C0_IDX);
    DL_GPIO_setPins(GPIO_DIR_PORT, GPIO_DIR_PIN_0_PIN);
    motor_couter[0]++;
    motor_location[0]+=6400/360;
    }
    else if(motor_couter[0]>0)
    {
    DL_GPIO_clearPins(GPIO_DIR_PORT, GPIO_DIR_PIN_0_PIN);
    DL_TimerA_setCaptureCompareValue(PWM_1_INST, 25, GPIO_PWM_1_C0_IDX);
    motor_couter[0]--;
    motor_location[0]-=6400/360;
    }
    else
    {

        DL_TimerA_setCaptureCompareValue(PWM_1_INST, 50, GPIO_PWM_1_C0_IDX);
    }
    if(motor_couter[1]<0)
    {
    DL_GPIO_setPins(GPIO_DIR_PORT, GPIO_DIR_PIN_1_PIN);
    DL_TimerA_setCaptureCompareValue(PWM_1_INST, 25, GPIO_PWM_1_C1_IDX);
    motor_couter[1]++;
    motor_location[1]+=6400/360;
    }
    else if(motor_couter[1]>0)
    {
    DL_GPIO_clearPins(GPIO_DIR_PORT, GPIO_DIR_PIN_1_PIN);
    DL_TimerA_setCaptureCompareValue(PWM_1_INST, 25, GPIO_PWM_1_C1_IDX);
    motor_couter[1]--;
    motor_location[1]-=6400/360;
    }
    else
    {

        DL_TimerA_setCaptureCompareValue(PWM_1_INST, 50, GPIO_PWM_1_C1_IDX);
    }
        
    DL_TimerA_clearInterruptStatus(PWM_1_INST,DL_TIMER_INTERRUPT_ZERO_EVENT);
    if(motor_couter[0]==0&&motor_couter[1]==0) 
    {
    READY_TO_GO = 1;
    }
    else {
    READY_TO_GO = 0;
    }
    }

}
void TIMER_0_INST_IRQHandler(void)
{
    #define VEL_TUNE 0  // 0=正常三环,进入位置环整定
    if (maix_data.flag) {
        // 计算小球速度（微分位置信号）并使用卡尔曼滤波
        float raw_vx = (maix_data.x - last_x) ; // 2ms周期
        float raw_vy = (maix_data.y - last_y) ;
        last_x = maix_data.x;
        last_y = maix_data.y;
        // ball_vx = vel_filter_alpha * ball_vx + (1.0f - vel_filter_alpha) * raw_vx;  // 移除低通滤波
        // ball_vy = vel_filter_alpha * ball_vy + (1.0f - vel_filter_alpha) * raw_vy;
        ball_vx = Kalman_Update(&kf_vx, raw_vx);
        ball_vy = Kalman_Update(&kf_vy, raw_vy);

        // 条件积分:小球一旦运动就清零位置积分,防止stick-slip过冲
        #define VEL_MOVE_THRESH 0.5f
        if(fabsf(ball_vx) > VEL_MOVE_THRESH || fabsf(ball_vy) > VEL_MOVE_THRESH) {
            pid3.location_sum = 0.0f;
            pid4.location_sum = 0.0f;
        }

        // 外环：位置误差 -> 目标速度
        // 圆形轨迹控制
        if(CYCLE_FLAG && CYCLE_TIME>0)
        {
            CYCLE_TIME--;
        // 计算圆轨迹目标点：当前位置角度 + 超前角度
        float dx = maix_data.x - CIRCLE_CX;
        float dy = maix_data.y - CIRCLE_CY;
        float current_angle = atan2f(dy, dx);  // 当前角度 (弧度)
        float target_angle = current_angle - (LEAD_ANGLE * 3.14159f / 180.0f);  // 超前角度 (顺时针)
        target_x = CIRCLE_CX + (int)(CIRCLE_R * cosf(target_angle));
        target_y = CIRCLE_CY + (int)(CIRCLE_R * sinf(target_angle));
        }
        else
        {
            if(maix_data.laser_flag)
            {
        // 激光控制：当存在激光时，目标位置改为激光坐标，
        target_x = maix_data.laser_x;
        target_y = maix_data.laser_y;
        }
        }
        #if VEL_TUNE
        float target_vx = 0.0f;  // 速度环整定:目标速度0,推球观察速度归零响应
        float target_vy = 0.0f;
        #else
        float target_vx = 0.013*PID_location(0, maix_data.x - target_x, &pid3); // 折中缩放
        float target_vy = 0.013*PID_location(0, maix_data.y - target_y, &pid4);
        #endif
        // 中环：速度误差 -> 目标角度
        float target_roll = SET0_R-PID_location(target_vx, ball_vx, &pid5);
        float target_pitch = SET0_P+PID_location(target_vy, ball_vy, &pid6);

        // 内环：角度误差 -> 电机控制
        motor_couter[0] += PID_location(target_roll, wit_data.roll, &pid1);
        motor_couter[1] += PID_location(target_pitch, wit_data.pitch, &pid2);
    } else {
        // 无数据时保持
        motor_couter[0] += PID_location(SET0_R, wit_data.roll, &pid1);
        motor_couter[1] += PID_location(SET0_P, wit_data.pitch, &pid2);
    }
}
void GROUP1_IRQHandler(void)
{
    switch (DL_Interrupt_getPendingGroup(DL_INTERRUPT_GROUP_1)) {
        case GPIO_KEY_INT_IIDX:

            if (!DL_GPIO_readPins(GPIO_KEY_PORT, GPIO_KEY_PIN_PIN)) {
                CYCLE_FLAG = 1;
                CYCLE_TIME = 1000;
            }
            break;
    }
}