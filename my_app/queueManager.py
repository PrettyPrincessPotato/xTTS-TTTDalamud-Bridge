import queue

# Clear the queue
def clear_queue(q):
    while not q.empty():
        try:
            q.get_nowait()  # Non-blocking get
        except queue.Empty:
            break  # The queue is empty
        q.task_done()  # Indicate that the item has been processed

# Create two queues, one for the requests and one for the audio data
request_queue = queue.Queue()
audio_queue = queue.Queue()

# Set the request_queue to the queue passed in, or create a new queue if none is passed in.
# This function is used to set the request_queue from the test script
# This is slowly turning into a misnomer, as it only really checks queue now, and request queue is created above.
def get_request_queue(runScript, q):
    if not runScript:
        global request_queue
        request_queue = q