

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
    def __init__(self, fixations, saccades, blinks, suggested_corrections, current_fixation, selected_fixation):
        if fixations is None:
            self.fixations = []
        else:
            self.fixations = fixations.copy()

        if saccades is None:
            self.saccades = []
        else:
            self.saccades = saccades.copy()

        if blinks is None:
            self.blinks = []
        else:
            self.blinks = blinks.copy()

        if suggested_corrections is None:
            self.suggested_corrections = []
        else:
            self.suggested_corrections = suggested_corrections.copy()

        self.current_fixation = current_fixation
        self.selected_fixation = selected_fixation

    def get_state(self):
        return self.fixations, self.saccades, self.blinks, self.suggested_corrections, self.current_fixation, self.selected_fixation