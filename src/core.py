import pandas as pd
import numpy as np
import time
from .state import History, Fix8State
from . import mini_emtk
from . import driftAlgorithms
from . import correction


ALGORITHM_REGISTRY = {
    "attach": ("line", driftAlgorithms.attach),
    "chain": ("line", driftAlgorithms.chain),
    "cluster": ("line", driftAlgorithms.cluster),
    "merge": ("line", driftAlgorithms.merge),
    "regress": ("line", driftAlgorithms.regress),
    "segment": ("line", driftAlgorithms.segment),
    "slice": ("line", driftAlgorithms.slice),
    "stretch": ("line", driftAlgorithms.stretch),
    "warp": ("word", driftAlgorithms.warp),
    "compare": ("word", driftAlgorithms.compare),
}


class Fix8Core:
    """
    Model class for Fix8.
    Stores and manages purely structural data (Pandas Dataframes, paths, states)
    and strictly non-GUI data operations previously built directly into Fix8.
    """
    def __init__(self):
        # fields relating to the stimulus
        self.image_file_path = None

        # fields relating to the trial folder
        self.folder_path = None
        self.trial_path = None
        self.trial_name = None

        # fields relating to fixations
        self.eye_events = None   # dataframe of eye events

        self.current_fixation = -1          # progress state
        self.suggested_corrections = None   # corrected fixations

        # field for tool undo/redo using memento pattern and state class
        self.state_history = History()

        # fields relating to AOIs
        self.aoi = None
        self.background_color = None

        # fields relating to the correction algorithm
        self.algorithm = "manual"
        self.algorithm_function = None
        self.secondary_algorithm_function = None
        self.suggested_fixation = None

        # keeps track of how many times file was saved so duplicates can be saved instead of overriding previous save file
        self.timer_start = 0  # beginning time of trial
        self.metadata = ""

        # fields relating to the drag and drop system
        self.selected_fixation = None           # clicked fixation
        self.xy = None
        self.locked_x = False

        # fields relating to aoi margin
        self.aoi_width = 7
        self.aoi_height = 4

    # ---------- Navigation ----------

    def previous_fixation(self):
        """Moves the active fixation cursor backwards."""
        if self.current_fixation > 0:
            self.current_fixation -= 1

    def next_fixation(self):
        """Moves the active fixation cursor forwards."""
        if self.eye_events is None or self.eye_events.empty:
            return

        if self.current_fixation < len(self.eye_events) - 1:
            self.current_fixation += 1

    # ---------- Manual edits ----------

    def update_fixation(self, index: int, new_x: float, new_y: float):
        """Manually corrects the position of a specific fixation."""
        if self.eye_events is None or self.eye_events.empty:
            return

        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if index < 0 or index >= len(fixations_only):
            return

        self.save_state()
        real_df_index = fixations_only.index[index]
        self.eye_events.at[real_df_index, 'x_cord'] = new_x
        self.eye_events.at[real_df_index, 'y_cord'] = new_y

    def delete_fixation(self, index: int):
        """Removes a fixation at the given index."""
        if self.eye_events is None or self.eye_events.empty:
            return

        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if index < 0 or index >= len(fixations_only):
            return

        self.save_state()
        real_df_index = fixations_only.index[index]
        self.eye_events = self.eye_events.drop(real_df_index).reset_index(drop=True)

        if self.suggested_corrections is not None and index < len(self.suggested_corrections):
            self.suggested_corrections = np.delete(self.suggested_corrections, index, axis=0)

        if self.current_fixation >= len(self.eye_events):
            self.current_fixation = len(self.eye_events) - 1

    # ---------- Line assignment ----------

    def _line_ys(self):
        if self.aoi is None or self.aoi.empty:
            return []
        return mini_emtk.find_lines_y(self.aoi)

    def assign_to_line(self, index: int, line_number: int):
        """Assigns fixation at `index` to the 1-based line number."""
        if self.eye_events is None:
            return
        line_ys = self._line_ys()
        if not line_ys or line_number < 1 or line_number > len(line_ys):
            return
        self.save_state()
        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if index < 0 or index >= len(fixations_only):
            return
        real_df_index = fixations_only.index[index]
        self.eye_events.at[real_df_index, 'y_cord'] = float(line_ys[line_number - 1])

    def assign_above(self, index: int):
        """Moves fixation to the nearest line above its current Y."""
        line_ys = self._line_ys()
        if not line_ys:
            return
        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if index < 0 or index >= len(fixations_only):
            return
        cur_y = float(fixations_only.iloc[index]['y_cord'])
        above = [y for y in line_ys if y < cur_y]
        if not above:
            return
        target = max(above)
        self.save_state()
        real_df_index = fixations_only.index[index]
        self.eye_events.at[real_df_index, 'y_cord'] = float(target)

    def assign_below(self, index: int):
        """Moves fixation to the nearest line below its current Y."""
        line_ys = self._line_ys()
        if not line_ys:
            return
        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if index < 0 or index >= len(fixations_only):
            return
        cur_y = float(fixations_only.iloc[index]['y_cord'])
        below = [y for y in line_ys if y > cur_y]
        if not below:
            return
        target = min(below)
        self.save_state()
        real_df_index = fixations_only.index[index]
        self.eye_events.at[real_df_index, 'y_cord'] = float(target)

    # ---------- Undo ----------

    def save_state(self):
        """Saves current state to history for undo functionality."""
        current_state = Fix8State(
            self.eye_events,
            self.suggested_corrections,
            self.current_fixation,
            self.selected_fixation,
        )
        self.state_history.set_state(current_state)

    def undo(self):
        """Restores the previous state from history. Returns True if a state was restored."""
        if self.state_history.is_empty():
            return False
        prev = self.state_history.get_state()
        eye_events, suggested, cur, sel = prev.get_state()
        self.eye_events = eye_events
        self.suggested_corrections = suggested
        self.current_fixation = cur
        self.selected_fixation = sel
        return True

    # ---------- AOI detection ----------

    def detect_aois(self, level="sub-line"):
        """Runs AOI detection on the stimulus image."""
        if not self.image_file_path:
            raise ValueError("No stimulus image loaded.")
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            level=level,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )
        return self.aoi

    # ---------- Correction algorithms ----------

    def run_algorithm(self, name: str, mode: str = "auto"):
        """
        Runs a correction algorithm by name.
        mode = "auto": applies corrections directly to eye_events
        mode = "assisted": stores suggested_corrections; user reviews each
        """
        if self.eye_events is None or self.eye_events.empty:
            raise ValueError("No fixation data loaded.")
        if name not in ALGORITHM_REGISTRY:
            raise ValueError(f"Unknown algorithm: {name}")
        if self.aoi is None or self.aoi.empty:
            self.detect_aois()

        input_kind, fn = ALGORITHM_REGISTRY[name]

        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        fixation_XY = np.array(fixations_only[['x_cord', 'y_cord']].values, dtype=float)

        if input_kind == "line":
            line_Y = np.array(mini_emtk.find_lines_y(self.aoi))
            corrected = fn(fixation_XY.copy(), line_Y)
        else:
            word_XY = np.array(mini_emtk.find_word_centers(self.aoi))
            corrected = fn(fixation_XY.copy(), word_XY)

        self.save_state()
        self.algorithm = name

        # `attach`, `chain`, etc mutate the second column in place; ensure shape (N,2)
        corrected = np.asarray(corrected, dtype=float)
        if corrected.ndim == 1:
            # algorithm returned just Ys — rebuild (x, y)
            corrected = np.column_stack([fixation_XY[:, 0], corrected])

        if mode == "auto":
            self._apply_corrections(corrected)
            self.suggested_corrections = None
        else:
            self.suggested_corrections = corrected
            self.current_fixation = 0

        return corrected

    def _apply_corrections(self, corrected_xy):
        """Writes corrected X,Y into eye_events for rows that are fixations."""
        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        for i, real_idx in enumerate(fixations_only.index):
            if i >= len(corrected_xy):
                break
            self.eye_events.at[real_idx, 'x_cord'] = float(corrected_xy[i, 0])
            self.eye_events.at[real_idx, 'y_cord'] = float(corrected_xy[i, 1])

    def accept_current_suggestion(self):
        """Accept the suggested correction for the current fixation and advance."""
        if self.suggested_corrections is None:
            return
        i = self.current_fixation
        if i < 0 or i >= len(self.suggested_corrections):
            return
        fixations_only = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if i >= len(fixations_only):
            return
        real_idx = fixations_only.index[i]
        self.save_state()
        self.eye_events.at[real_idx, 'x_cord'] = float(self.suggested_corrections[i, 0])
        self.eye_events.at[real_idx, 'y_cord'] = float(self.suggested_corrections[i, 1])
        self.next_fixation()

    def accept_all_suggestions(self):
        """Applies all suggested corrections at once."""
        if self.suggested_corrections is None:
            return
        self.save_state()
        self._apply_corrections(self.suggested_corrections)
        self.suggested_corrections = None

    # ---------- Filters ----------

    def filter_lowpass_duration(self, threshold_ms):
        """Remove fixations shorter than threshold_ms."""
        if self.eye_events is None:
            return
        self.save_state()
        mask = (self.eye_events['eye_event'] != 'fixation') | (self.eye_events['duration'] >= threshold_ms)
        self.eye_events = self.eye_events[mask].reset_index(drop=True)

    def filter_highpass_duration(self, threshold_ms):
        """Remove fixations longer than threshold_ms."""
        if self.eye_events is None:
            return
        self.save_state()
        mask = (self.eye_events['eye_event'] != 'fixation') | (self.eye_events['duration'] <= threshold_ms)
        self.eye_events = self.eye_events[mask].reset_index(drop=True)

    def filter_outlier_duration(self, std_threshold):
        """Remove fixations whose duration is beyond `std_threshold` std devs from the mean."""
        if self.eye_events is None:
            return
        fix = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if fix.empty:
            return
        mean = fix['duration'].mean()
        std = fix['duration'].std()
        if std == 0 or pd.isna(std):
            return
        lo, hi = mean - std_threshold * std, mean + std_threshold * std
        self.save_state()
        mask = (
            (self.eye_events['eye_event'] != 'fixation')
            | ((self.eye_events['duration'] >= lo) & (self.eye_events['duration'] <= hi))
        )
        self.eye_events = self.eye_events[mask].reset_index(drop=True)

    def filter_outside_screen(self, width, height):
        """Remove fixations that fall outside the stimulus image bounds."""
        if self.eye_events is None:
            return
        self.save_state()
        mask = (
            (self.eye_events['eye_event'] != 'fixation')
            | (
                (self.eye_events['x_cord'] >= 0)
                & (self.eye_events['x_cord'] < width)
                & (self.eye_events['y_cord'] >= 0)
                & (self.eye_events['y_cord'] < height)
            )
        )
        self.eye_events = self.eye_events[mask].reset_index(drop=True)

    def merge_short_fixations(self, duration_threshold, dispersion_threshold):
        """Merge consecutive short fixations that are close together into one."""
        if self.eye_events is None:
            return
        fix_df = self.eye_events[self.eye_events['eye_event'] == 'fixation'].reset_index(drop=True)
        if len(fix_df) < 2:
            return
        self.save_state()

        merged_rows = []
        i = 0
        rows = fix_df.to_dict('records')
        while i < len(rows):
            cur = dict(rows[i])
            j = i + 1
            while j < len(rows):
                nxt = rows[j]
                gap = ((cur['x_cord'] - nxt['x_cord']) ** 2 + (cur['y_cord'] - nxt['y_cord']) ** 2) ** 0.5
                if cur['duration'] < duration_threshold and gap < dispersion_threshold:
                    tot = cur['duration'] + nxt['duration']
                    if tot > 0:
                        cur['x_cord'] = (cur['x_cord'] * cur['duration'] + nxt['x_cord'] * nxt['duration']) / tot
                        cur['y_cord'] = (cur['y_cord'] * cur['duration'] + nxt['y_cord'] * nxt['duration']) / tot
                    cur['duration'] = tot
                    j += 1
                else:
                    break
            merged_rows.append(cur)
            i = j if j > i + 1 else i + 1

        new_df = pd.DataFrame(merged_rows)
        new_df['eye_event'] = 'fixation'
        self.eye_events = new_df.reset_index(drop=True)

    # ---------- Distortions (kept from original) ----------

    def apply_noise(self, threshold):
        self.metadata += f"generate,noise {threshold},{time.time()}\n"
        self.save_state()
        self.eye_events["x_cord"] = self.eye_events["x_cord"] + np.random.normal(0, threshold, self.eye_events.shape[0])
        self.eye_events["y_cord"] = self.eye_events["y_cord"] + np.random.normal(0, threshold, self.eye_events.shape[0])
        if self.algorithm != "manual" and self.suggested_corrections is not None:
            self.suggested_corrections[:, 0] = self.eye_events["x_cord"]

    def apply_slope(self, threshold):
        self.metadata += f"generate,slope {threshold},{time.time()}\n"
        self.save_state()
        original_fixations = np.array(self.eye_events[['x_cord', 'y_cord', 'duration']])
        fixations = np.array(mini_emtk.error_droop(threshold, original_fixations))
        self.eye_events["x_cord"] = fixations[:, 0]
        self.eye_events["y_cord"] = fixations[:, 1]
        self.eye_events["duration"] = fixations[:, 2]

    def apply_offset(self, threshold):
        self.metadata += f"generate,offset {threshold},{time.time()}\n"
        self.save_state()
        original_fixations = np.array(self.eye_events[['x_cord', 'y_cord', 'duration']])
        fixations = np.array(mini_emtk.error_offset(threshold, original_fixations))
        self.eye_events["x_cord"] = fixations[:, 0]
        self.eye_events["y_cord"] = fixations[:, 1]
        self.eye_events["duration"] = fixations[:, 2]

    def apply_shift(self, threshold):
        self.metadata += f"generate,shift {threshold},{time.time()}\n"
        self.save_state()
        self.aoi, self.background_color = mini_emtk.EMTK_find_aoi(
            self.image_file_path,
            margin_height=self.aoi_height,
            margin_width=self.aoi_width,
        )
        line_Y = mini_emtk.find_lines_y(self.aoi)
        original_fixations = np.array(self.eye_events[['x_cord', 'y_cord', 'duration']])
        fixations = np.array(mini_emtk.error_shift(threshold, line_Y, original_fixations))
        self.eye_events["x_cord"] = fixations[:, 0]
        self.eye_events["y_cord"] = fixations[:, 1]
        self.eye_events["duration"] = fixations[:, 2]

    # ---------- Statistics ----------

    def trial_stats(self):
        """Returns a dict of statistics for the current trial."""
        if self.eye_events is None or self.eye_events.empty:
            return {}
        fix = self.eye_events[self.eye_events['eye_event'] == 'fixation']
        if fix.empty:
            return {}
        return {
            "fixation_count": int(len(fix)),
            "trial_duration_ms": float(fix['duration'].sum()),
            "max_duration_ms": float(fix['duration'].max()),
            "min_duration_ms": float(fix['duration'].min()),
            "mean_duration_ms": float(fix['duration'].mean()),
            "aoi_count": 0 if self.aoi is None else int(len(self.aoi)),
        }


