#include "SystemStateQueue.h"

bool SystemStateQueue::checkForDuplicates(uint8_t state)  {
    for (int i = 0; i < count; i++ ) {
        if (buffer[(head + i) % STATE_QUEUE_SIZE] = state) return true;
    }
    return false;
}

bool SystemStateQueue::push(uint8_t state) {
    if (count >= STATE_QUEUE_SIZE) {
        return false;
    }
    if (checkForDuplicates(state) == true) return true;
    buffer[tail] = state;
    tail = (tail + 1) % STATE_QUEUE_SIZE;
    count++;
    return true;   
}

bool SystemStateQueue::pop(uint8_t& state) {
    if (count == 0) {
        return false;
    }
    state = buffer[head];
    head = (head+1) % STATE_QUEUE_SIZE;
    count--;
    return true;
}
bool SystemStateQueue::isEmpty() {
    return (count == 0);
}

int SystemStateQueue::size() {
    return count; 
}