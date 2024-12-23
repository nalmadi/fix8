

# this is needed for undo/redo feature
# implemented using the Memento pattern

class History:
    def __init__(self):
        # holds Fix8State objects
        self.states = []

    def is_empty(self):
        return len(self.states) == 0

    def get_state(self):
        return self.states.pop()
    
    def set_state(self, state):
        self.states.append(state)
        

class Fix8State:
    def __init__(self, eye_events, suggested_corrections, current_fixation, selected_fixation):
        
        if eye_events is None:
            self.eye_events = None
        else:
            self.eye_events = eye_events.copy()

        if suggested_corrections is None:
            self.suggested_corrections = []
        else:
            self.suggested_corrections = suggested_corrections.copy()

        self.current_fixation = current_fixation
        self.selected_fixation = selected_fixation

    def get_state(self):
        return self.eye_events, self.suggested_corrections, self.current_fixation, self.selected_fixation