"""
This file is used to submit tasks to the distributed task queue.
This file must exist on the file-server (e.g. via rsync) and must be run on the file-server (see train
"""

from app import deep_learning_task


NUM_WORKERS = 8

if __name__ == "__main__":

    # example: compute deep_learning_task with 128 hidden units on 4 nodes and 256 on another 4 nodes
    for n in range(NUM_WORKERS // 2):
        deep_learning_task.delay(num_hidden_units=128)
    for n in range(NUM_WORKERS // 2):
        deep_learning_task.delay(num_hidden_units=256)
