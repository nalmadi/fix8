

######################## from EMTK #################################


from PIL import Image
import pandas as pd
import numpy as np

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