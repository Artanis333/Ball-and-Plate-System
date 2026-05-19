#include "wit.h"

uint8_t wit_dmaBuffer[33];
uint8_t maix_dmaBuffer[6];

WIT_Data_t wit_data;
MAIX_Data_t maix_data;

void WIT_Init(void)
{
    DL_DMA_setSrcAddr(DMA, DMA_WIT_CHAN_ID, (uint32_t)(&UART_WIT_INST->RXDATA));
    DL_DMA_setDestAddr(DMA, DMA_WIT_CHAN_ID, (uint32_t) &wit_dmaBuffer[0]);
    DL_DMA_setTransferSize(DMA, DMA_WIT_CHAN_ID, 32);
    DL_DMA_enableChannel(DMA, DMA_WIT_CHAN_ID);

    NVIC_EnableIRQ(UART_WIT_INST_INT_IRQN);
}
void MAIX_Init(void)
{
    DL_DMA_setSrcAddr(DMA, DMA_MAIX_CHAN_ID, (uint32_t)(&UART_MAIX_INST->RXDATA));
    DL_DMA_setDestAddr(DMA, DMA_MAIX_CHAN_ID, (uint32_t) &maix_dmaBuffer[0]);
    DL_DMA_setTransferSize(DMA, DMA_MAIX_CHAN_ID, 2);
    DL_DMA_enableChannel(DMA, DMA_MAIX_CHAN_ID);

    NVIC_EnableIRQ(UART_MAIX_INST_INT_IRQN);
}