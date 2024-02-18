

######################## from EMTK #################################


from PIL import Image
import pandas as pd
import numpy as np
import random
import os

def find_background_color(img):
    """Private function that identifies the background color of the image
    Parameters
    ----------
    img : PIL.Image
        a PIL (pillow fork) Image object
    Returns
    -------
    str
        the color of the background of the image
    """

    img = img.convert("L")  # Convert to grayscale
    threshold = 80
    img = img.point(
        lambda x: 0 if x < threshold else 255, "1"
    )  # Apply threshold and convert to black and white

    width, height = img.size

    color_result = []
    box_size = min(width, height) // 20

    # Move a tiny rectangle box to obtain most common color
    for x, y in zip(range(0, width, box_size), range(0, height, box_size)):
        box = (x, y, x + box_size, y + box_size)
        minimum, maximum = img.crop(box).getextrema()
        color_result.append(minimum)
        color_result.append(maximum)

    # Analyze and determine the background color
    if color_result.count(255) > color_result.count(0):
        bg_color = "white"
    else:
        bg_color = "black"

    return bg_color

def EMTK_find_aoi(image_file_name=None, img=None, level="sub-line", margin_height=4, margin_width=7):
    """Find Area of Interest in the given image and store the aoi attributes in a Pandas Dataframe
    Parameters
    ----------
    image : str
        filename for the image, e.g. "vehicle_java.jpg"
    image_path : str
        path for all images, e.g. "emip_dataset/stimuli/"
    img : PIL.Image, optional
        PIL.Image object if user chooses to input an PIL image object
    level : str, optional
        level of detection in AOIs, "line" for each line as an AOI or "sub-line" for each token as an AOI
    margin_height : int, optional
        marginal height when finding AOIs, use smaller number for tight text layout
    margin_width : int, optional
        marginal width when finding AOIs, use smaller number for tight text layout
    Returns
    -------
    pandas.DataFrame
        a pandas DataFrame of area of interest detected by the method
    """

    if img is None:
        if image_file_name is None:
            return
        
        # img = Image.open(image_path + image).convert('1')
        img = Image.open(image_file_name)
        img = img.convert("L")  # Convert to grayscale
        threshold = 80
        img = img.point(
            lambda x: 0 if x < threshold else 255, "1"
        )  # Apply threshold and convert to black and white

    else:
        img = img.convert("L")  # Convert to grayscale
        threshold = 80
        img = img.point(
            lambda x: 0 if x < threshold else 255, "1"
        )  # Apply threshold and convert to black and white

    width, height = img.size

    # Detect the background color
    bg_color = find_background_color(img)
    # print("bg_color: ", bg_color)

    left, right = 0, width

    vertical_result, upper_bounds, lower_bounds = [], [], []

    # Move the detecting rectangle from the top to the bottom of the image
    for upper in range(height - margin_height):
        lower = upper + margin_height

        box = (left, upper, right, lower)
        minimum, maximum = img.crop(box).getextrema()

        if upper > 1:
            if bg_color == "black":
                if vertical_result[-1][3] == 0 and maximum == 255:
                    # Rectangle detects white color for the first time in a while -> Start of one line
                    upper_bounds.append(upper)
                if vertical_result[-1][3] == 255 and maximum == 0:
                    # Rectangle detects black color for the first time in a while -> End of one line
                    lower_bounds.append(lower)
            elif bg_color == "white":
                if vertical_result[-1][2] == 255 and minimum == 0:
                    # Rectangle detects black color for the first time in a while -> Start of one line
                    upper_bounds.append(upper)
                if vertical_result[-1][2] == 0 and minimum == 255:
                    # Rectangle detects white color for the first time in a while -> End of one line
                    lower_bounds.append(lower)

        # Storing all detection result
        vertical_result.append([upper, lower, minimum, maximum])

    final_result = []

    line_count = 1

    # Iterate through each line of code from detection
    for upper_bound, lower_bound in list(zip(upper_bounds, lower_bounds)):
        # Reset all temporary result for the next line
        horizontal_result, left_bounds, right_bounds = [], [], []

        # Move the detecting rectangle from the left to the right of the image
        for left in range(width - margin_width):
            right = left + margin_width

            box = (left, upper_bound, right, lower_bound)
            minimum, maximum = img.crop(box).getextrema()

            if left > 1:
                if bg_color == "black":
                    if horizontal_result[-1][3] == 0 and maximum == 255:
                        # Rectangle detects black color for the first time in a while -> Start of one word
                        left_bounds.append(left)
                    if horizontal_result[-1][3] == 255 and maximum == 0:
                        # Rectangle detects white color for the first time in a while -> End of one word
                        right_bounds.append(right)
                elif bg_color == "white":
                    if horizontal_result[-1][2] == 255 and minimum == 0:
                        # Rectangle detects black color for the first time in a while -> Start of one word
                        left_bounds.append(left)
                    if horizontal_result[-1][2] == 0 and minimum == 255:
                        # Rectangle detects white color for the first time in a while -> End of one word
                        right_bounds.append(right)

            # Storing all detection result
            horizontal_result.append([left, right, minimum, maximum])

        if level == "sub-line":
            part_count = 1

            for left, right in list(zip(left_bounds, right_bounds)):
                final_result.append(
                    [
                        "sub-line",
                        f"line {line_count} part {part_count}",
                        left,
                        upper_bound,
                        right,
                        lower_bound,
                    ]
                )
                part_count += 1

        elif level == "line":
            final_result.append(
                [
                    "line",
                    f"line {line_count}",
                    left_bounds[0],
                    upper_bound,
                    right_bounds[-1],
                    lower_bound,
                ]
            )

        line_count += 1

    # Format pandas dataframe
    columns = ["kind", "name", "x", "y", "width", "height", "image"]
    aoi = pd.DataFrame(columns=columns)

    for entry in final_result:
        kind, name, x, y, x0, y0 = entry
        width = x0 - x
        height = y0 - y
        image = image_file_name.split("/")[-1]

        # For better visualization
        x += margin_width / 2
        width -= margin_width

        value = [kind, name, x, y, width, height, image]
        dic = dict(zip(columns, value))

        aoi = aoi.append(dic, ignore_index=True)

    return aoi, bg_color


# modified from EMTK
def read_EyeLink1000_experiment(filename, destination_path):
    """Read asc file from Eye Link 1000 eye tracker

    Parameters
    ----------
    filename : str
        name of the asc file
        
    filetype : str
        filetype of the file, e.g. "tsv"
    """

    asc_file = open(filename)
    print("parsing file:", filename)

    text = asc_file.read()
    text_lines = text.split('\n')

    trial_id = -1
    participant_id = filename.split('/')[-1].replace('.asc', '')

    header = ["time_stamp", "eye_event", "x_cord", "y_cord", "duration", "pupil", "x1_cord", "y1_cord", "amplitude", "peak_velocity"]
    result = pd.DataFrame(columns=header)

    count = 0

    for line in text_lines:

        token = line.split()

        if not token:
            continue

        if 'DISPLAY_COORDS' in token:

            display_width = int(token[-2])
            display_height = int(token[-1])

        if "TRIALID" in token:
            # List of eye events
            if trial_id == -1:
                trial_id = int(token[-1])
                continue

            # Read image location
            index = str(int(trial_id) + 1)
            experiment = participant_id
            runtime_folder_path = '/'.join(filename.split('/')[:-1])
            location = runtime_folder_path + '/runtime/dataviewer/' + experiment + '/graphics/VC_' + index + '.vcl'
            with open(location, 'r') as file:
                target_line = file.readlines()[1]
                tokens = target_line.split()
                image = tokens[-3]
                x_offset = tokens[-2]
                y_offset = tokens[-1]
                
            result['trial_id'] = trial_id + 1
            result['participant_id'] = participant_id
            result['image'] = image
            
            # create a folder with trial number at destination_path
            trial_folder = destination_path + '/P_' + str(experiment) + '/' + str(trial_id  + 1) + '/'
            if not os.path.exists(trial_folder):
                os.makedirs(trial_folder)

            result.to_csv(trial_folder + 'P' + str(experiment) + '_T' + str(trial_id  + 1) + '.csv')

            # create a black background image with the same size as the display
            img = Image.new('RGB', (display_width, display_height), color = 'black')

            # overlay image on the black background with the offset keeping transparent background
            layer = Image.open(location.split('VC')[0] + '../../' + image).convert('RGBA')
            img.paste(layer, (int(x_offset), int(y_offset)), mask=layer) 

            # save the image to the folder
            img.save(trial_folder + str(trial_id  + 1) + '.png')

            # copy the image to the folder
            os.system('cp ' + location + ' ' + trial_folder)

            result = pd.DataFrame(columns=header)
            count = 0
            trial_id = int(token[-1])

        if token[0] == "EFIX":
            timestamp = int(token[2])
            duration = int(token[4])
            x_cord = float(token[5])
            y_cord = float(token[6])
            pupil = int(token[7])

            df = pd.DataFrame([[timestamp,
                                    "fixation",
                                    x_cord,
                                    y_cord,
                                    duration,
                                    pupil,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan]], columns=header)
            
            result = result.append(df, ignore_index=True)
            count += 1

        if token[0] == "ESACC":
            timestamp = int(token[2])
            duration = int(token[4])
            x_cord = float(token[5]) if token[5] != '.' else 0.0
            y_cord = float(token[6]) if token[6] != '.' else 0.0
            x1_cord = float(token[7]) if token[7] != '.' else 0.0
            y1_cord = float(token[8]) if token[8] != '.' else 0.0
            amplitude = float(token[9])
            peak_velocity = int(token[10])
            
            df = pd.DataFrame([[timestamp,
                                    "saccade",
                                    x_cord,
                                    y_cord,
                                    duration,
                                    np.nan,
                                    x1_cord,
                                    y1_cord,
                                    amplitude,
                                    peak_velocity]], columns=header)
            
            result = result.append(df, ignore_index=True)
            count += 1

        if token[0] == "EBLINK":
            timestamp = int(token[2])
            duration = int(token[4])
            df = pd.DataFrame([[timestamp,
                                    "blink",
                                    np.nan,
                                    np.nan,
                                    duration,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan]], columns=header)
            
            result = result.append(df, ignore_index=True)
            count += 1

    # Read image location
    index = str(int(trial_id) + 1)
    experiment = participant_id.split('/')[-1]
    runtime_folder_path = '/'.join(filename.split('/')[:-1])
    location = runtime_folder_path + '/runtime/dataviewer/' + experiment + '/graphics/VC_' + index + '.vcl'
    with open(location, 'r') as file:
        target_line = file.readlines()[1]
        tokens = target_line.split()
        image = tokens[-3]
        x_offset = tokens[-2]
        y_offset = tokens[-1]
        
    result['trial_id'] = trial_id + 1
    result['participant_id'] = participant_id
    result['image'] = image
    
    # create a folder with trial number at destination_path
    trial_folder = destination_path + '/P_' + str(experiment) + '/' + str(trial_id + 1) + '/'
    if not os.path.exists(trial_folder):
        os.makedirs(trial_folder)

    result.to_csv(trial_folder + 'P' + str(experiment) + '_T' + str(trial_id + 1) + '.csv')

    # create a black background image with the same size as the display
    img = Image.new('RGB', (display_width, display_height), color = 'black')

    # overlay image on the black background with the offset keeping transparent background
    layer = Image.open(location.split('VC')[0] + '../../' + image).convert('RGBA')
    img.paste(layer, (int(x_offset), int(y_offset)), mask=layer) 

    # save the image to the folder
    img.save(trial_folder + str(trial_id + 1) + '.png')

    # copy the image to the folder
    os.system('cp ' + location + ' ' + trial_folder)

    asc_file.close()


######################## end from EMTK #################################

def distance(fix1, fix2):
    ''' returns distance between two fixations '''
    return ((fix1[0] - fix2[0])**2 + (fix1[1] - fix2[1])**2)**0.5



def read_EyeLink1000(filename, filepath):
    """Read asc file from Eye Link 1000 eye tracker and write a result in a csv file.
    Parameters
    ----------
    filename : str
        name of the asc file
    filepath : str
        filepath to write the csv file
        
    Returns
    -------
    pandas.DataFrame
        DataFrame with the data from the asc file
    """

    asc_file = open(filename)
    print("parsing file:", filename)

    text = asc_file.read()
    text_lines = text.split('\n')

    trial_id = -1
    participant_id = filename.split('.')[0]

    count = 0

    header = ["time_stamp", "eye_event", "x_cord", "y_cord", "duration", "pupil", "x1_cord", "y1_cord", "amplitude", "peak_velocity"]
    result = pd.DataFrame(columns=header)

    for line in text_lines:

        token = line.split()

        if not token:
            continue

        if "TRIALID" in token:
            # List of eye events
            if trial_id == -1:
                trial_id = int(token[-1])
                continue

            count = 0
            trial_id = int(token[-1])

        # at end of fixation event
        if token[0] == "EFIX":
            timestamp = int(token[2])
            duration = int(token[4])
            x_cord = float(token[5])
            y_cord = float(token[6])
            pupil = int(token[7])

            df = pd.DataFrame([[timestamp,
                                    "fixation",
                                    x_cord,
                                    y_cord,
                                    duration,
                                    pupil,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan]], columns=header)
            
            result = result.append(df, ignore_index=True)

            count += 1

        # at end of saccade event
        if token[0] == "ESACC":
            timestamp = int(token[2])
            duration = int(token[4])
            x_cord = float(token[5]) if token[5] != '.' else 0.0
            y_cord = float(token[6]) if token[6] != '.' else 0.0
            x1_cord = float(token[7]) if token[7] != '.' else 0.0
            y1_cord = float(token[8]) if token[8] != '.' else 0.0
            amplitude = float(token[9])
            peak_velocity = int(token[10])

            df = pd.DataFrame([[timestamp,
                                    "saccade",
                                    x_cord,
                                    y_cord,
                                    duration,
                                    np.nan,
                                    x1_cord,
                                    y1_cord,
                                    amplitude,
                                    peak_velocity]], columns=header)
            
            result = result.append(df, ignore_index=True)

            count += 1

        # at end of blink event
        if token[0] == "EBLINK":
            timestamp = int(token[2])
            duration = int(token[4])

            df = pd.DataFrame([[timestamp,
                                    "blink",
                                    np.nan,
                                    np.nan,
                                    duration,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan,
                                    np.nan]], columns=header)
            
            result = result.append(df, ignore_index=True)

            count += 1

    asc_file.close()

    result.to_csv(filepath)
    print("Wrote a csv file to: " + filepath)
    return result

#######################
##### From Correction.y
#######################

def generate_fixations_left(aois_with_tokens, dispersion):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """

    fixations = []

    for index, row in aois_with_tokens.iterrows():
        x, y, width, height = (
            row["x"],
            row["y"],
            row["width"],
            row["height"]
        )

        fixation_x = x + width / 3  + random.randint(-dispersion, dispersion)
        fixation_y = y + height / 2  + random.randint(-dispersion, dispersion)

        fixations.append([fixation_x, fixation_y, width * 3])

    return fixations


def generate_fixations_left_skip(aois_with_tokens, skip_probability):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also skips short words with a probability
    defined by the user

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    skip_probability : float
        probability of skipping a word

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """

    fixations = []
    word_count = 0
    skip_count = 0

    for index, row in aois_with_tokens.iterrows():
        x, y, width, height = (
            row["x"],
            row["y"],
            row["width"],
            row["height"]

        )

        word_count += 1

        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)

        if random.random() < skip_probability:
            skip_count += 1 
        else:
            fixations.append([fixation_x, fixation_y, width * 3])

    # print(skip_count / word_count)
    return fixations


def within_line_regression(aois_with_tokens, regression_probability):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also simulates WITHIN-line regressions
    with a probability defined by the user

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    regression_probability : float
        probability of regression

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """
        
    fixations = []

    aoi_list = aois_with_tokens.values.tolist()

    # pick regression indexes
    regression_indexes = []
    for index, row in aois_with_tokens.iterrows():
        if index > 2 and random.random() < regression_probability / 10:
            regression_indexes.append(index)

    # pick at least one regression index if probability is not 0
    if len(regression_indexes) == 0 and regression_probability > 0:
        regression_indexes.append(random.randint(2, len(aoi_list)-1))


    index = 0
    while index < len(aoi_list):
        # x, y, width, height, token = (
        x, y, width, height = (
                                aoi_list[index][2],
                                aoi_list[index][3],
                                aoi_list[index][4],
                                aoi_list[index][5],
                                #aoi_list[index][7],
                                )

        line = int(str(aoi_list[index][1]).split(" ")[1])

        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)
        duration = 100 + (width/15) * 40

        fixations.append([fixation_x, fixation_y, duration])

        if index in regression_indexes:
            regression_indexes.remove(index)
            rand_index = random.randint(index-10, index-1)

            attempts = 0

            # keep trying to find a word on a different line
            while (
                int(str(aoi_list[rand_index][1]).split(" ")[1]) != line
                and attempts < 10
            ):
                rand_index = random.randint(0, index-1)
                attempts += 1

            if attempts != 10:
                index = rand_index

        index += 1

    return fixations


def between_line_regression(aois_with_tokens, regression_probability):
    """
    function to generate fixations at the optimal viewing poisiton slightly to
    the left of the center of each word, also simulates BETWEEN-line regressions
    with a probability defined by the user

    Parameters
    ----------
    aois_with_tokens : pandas.DataFrame
        a dataframe containing the AOIs and tokens

    regression_probability : float
        probability of regression

    Returns
    ----------
    fixations : list
        a list of generated fixations
    """
        
    fixations = []

    aoi_list = aois_with_tokens.values.tolist()

    # pick regression indexes
    regression_indexes = []
    for index, row in aois_with_tokens.iterrows():
        if index > 2 and random.random() < regression_probability / 10:
            regression_indexes.append(index)

    # pick at least one regression index if probability is not 0
    if len(regression_indexes) == 0 and regression_probability > 0:
        regression_indexes.append(random.randint(2, len(aoi_list)-1))


    index = 0
    while index < len(aoi_list):
        # x, y, width, height, token = (
        x, y, width, height = (
                                aoi_list[index][2],
                                aoi_list[index][3],
                                aoi_list[index][4],
                                aoi_list[index][5],
                                #aoi_list[index][7],
                                )

        line = int(str(aoi_list[index][1]).split(" ")[1])

        fixation_x = x + width / 3 + random.randint(-10, 10)
        fixation_y = y + height / 2 + random.randint(-10, 10)
        duration = 100 + (width/15) * 40

        fixations.append([fixation_x, fixation_y, duration])

        if index in regression_indexes:
            regression_indexes.remove(index)
            rand_index = random.randint(0, index-1)

            attempts = 0

            # keep trying to find a word on a different line
            while (
                int(str(aoi_list[rand_index][1]).split(" ")[1]) == line
                and attempts < 10
            ):
                rand_index = random.randint(0, index-1)
                attempts += 1

            if attempts != 10:
                index = rand_index

        index += 1

    return fixations


def error_offset(y_offset, fixations):
    """
    Introduces an offset distortion to the fixations

    Parameters
    ----------
    x_offset : int
        offset in the x direction

    y_offset : int
        offset in the y direction

    fixations : list
        a list of fixations

    Returns
    ----------
    fixations : list
        a list of distorted fixations
    """

    results = []

    for fix in fixations:
        x, y = fix[0], fix[1]
        results.append([x, y + y_offset, fix[2]])

    return results


def error_shift(y_shift_factor, line_ys, fixations):
    """
    Introduces a shift distortion to the fixations

    Parameters
    ----------
    y_shift_factor : float
        shift factor

    line_ys : list
        a list of line Ys
        
    fixations : list
        a list of fixations

    Returns
    ----------
    fixations : list
        a list of distorted fixations
    """

    results = []

    line_height = line_ys[1] - line_ys[0]

    for fix in fixations:
        x, y = fix[0], fix[1]

        distance_from_first_line = abs(y - line_ys[0])

        results.append(
            [x, y + ((distance_from_first_line/line_height*2) * y_shift_factor/2), fix[2]]
        )


    return results



def error_droop(droop_factor, fixations):
    """
    Introduces a slope/droop distortion to the fixations

    Parameters
    ----------
    droop_factor : float
        droop factor
        
    fixations : list
        a list of fixations

    Returns
    ----------
    fixations : list
        a list of distorted fixations
    """

    results = []

    first_x = fixations[0][0]

    for fix in fixations:
        x, y = fix[0], fix[1]

        results.append([x, y + ((x - first_x) / 100 * droop_factor), fix[2]])

    return results