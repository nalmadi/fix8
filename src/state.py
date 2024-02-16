

# this is needed for undo/redo feature
# implemented using the Memento pattern

class State:
    def __init__(self):
        self.states = []

    def is_empty(self):
        return len(self.states) == 0

    def get_state(self):
        return self.states.pop()
    
    def set_state(self, state):
        self.states.append(state.copy())
        