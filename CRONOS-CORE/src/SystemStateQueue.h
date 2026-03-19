#pragma once

#include <Arduino.h>

#define STATE_QUEUE_SIZE 20

class SystemStateQueue {
    protected: 
        uint8_t buffer[STATE_QUEUE_SIZE];
        int head = 0;
        int tail = 0;
        int count = 0; 
        bool checkForDuplicates(uint8_t state);
    public: 
        bool push(uint8_t state);
        bool pop(uint8_t &state);
        bool isEmpty();
        int size();

};
