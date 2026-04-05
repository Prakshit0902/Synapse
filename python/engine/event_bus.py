import queue

# Ye dabba poore project mein ek hi rahega
UI_STATE_QUEUE = queue.Queue()

def broadcast_state(type_name, data=None):
    message = {"type": type_name}
    if data is not None:
        message.update(data)
    UI_STATE_QUEUE.put(message)