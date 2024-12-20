# Fix8 Overview

Fix8 (Fixate) is an open-source GUI Tool for working with eye tracking data in reading tasks. FIx8 includes a novel semi-automated correction approach for eye tracking data in reading tasks.  The proposed approach allows the user to collaborate with an algorithm to produce accurate corrections in less time without sacrificing accuracy.


[![Watch the video](./src/.images/step2.jpg)](https://youtu.be/Zw2uO3IE2vI?si=h1yYnNQag-0Q7lVe)




# Main Features ⭐

- Drift correction including manual, assisted (semi-automated), and automated correction.
- Fully customizable and interactive visualization.
- Synthetic data and distortion generation including full control of word skipping, within-line and between-line regressions.
- Filters: high-pass, low-pass, outlier, merge, and outside screen filters.
- Analyses and reports including hit-test and eye movement metrics like Fixation count, First-Fixation Duration, Single-Fixation Duration, and Total Time.
- Data Converters: EyeLink data, ASCII, CSV, and JSON are supported.
- Request a feature by making an issue in this repository!


# Manual 📖
A comprehensive manual of Fix8 GUI and every feature can be found here: [Fix8_Manual_v1.2](https://docs.google.com/document/d/14g-kQfCTfn-jabcN50_mCkjD39DFVtT_sLlosPTREzQ/edit?usp=sharing)



# Executables 💻

- Windows: 

    Compressed executable (single file): <a id="raw-url" href="https://github.com/nalmadi/fix8/tree/main/executables/Fix8_v1.1_onefile.zip">[Download]</a> 

    UNcompressed executable (many files): <a id="raw-url" href="https://github.com/nalmadi/fix8/tree/main/executables/Fix8_v1.1.zip">[Download]</a>

  
    > to download and run Fix8 do the following:
    >- Click on one of the download link above.
    >- In the top right, right-click the **Raw** button.
    >- Click on "Save as..."
    >- Unzip the file.
    >- Locate Fix8.exe and run it, first run might take a minute.
    >- Enjoy!

- Mac:

    Compressed executable (single file): <a id="raw-url" href="https://github.com/nalmadi/fix8/blob/main/executables/fix8_Mac.zip">[Download]</a>

- Linux:

    Coming soon!


# Run Fix8 from code 🚀
To run Fix8 from the Python code, follow these steps:

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/nalmadi/fix8.git
    cd fix8
    ```

2. **Create a Virtual Environment:**

    It's recommended to use a virtual environment to manage dependencies and isolate your project's environment:

    ```bash
    python -m venv myvenv
    ```

    Activate the virtual environment:
    
    **On Windows:**
    
    ```bash
    myvenv\Scripts\activate
    ```

    **On macOS and Linux:**
    
    ```bash
    source myvenv/bin/activate
    ```

3. **Install Requirements:**

    Once the virtual environment is activated, install the package via pip:

    ```bash
    pip install .
    ```

    If you plan to make changes to the code and rerun the package with the new changes, use this command instead:

   ```bash
   pip install -e .
   ```

5. **Run the Tool:**

    Once done, run the tool simply by entering the command "fix8" in the terminal:

    ```bash
    fix8
    ```


6. **Deactivate the Virtual Environment:**

    When you're done using the tool, deactivate the virtual environment:

    ```bash
    deactivate
    ```



# Keyboard Shortcuts ⌨️​
[![Keyboard shortcuts](./src/.images/fix8-keyboard.png)](https://youtu.be/Zw2uO3IE2vI?si=h1yYnNQag-0Q7lVe)



| Key         | Functionality                               |
| ----------- | ------------------------------------------- |
| a           | assign current fixation to line above       |
| z           | assign current fixation to line below       |
| space       | accept suggestion                           |
| backspace   | delete fixation (click on fixation to select)|
| right       | next fixation                               |
| left        | previous fixation                           |
| 1-9         | assign fixation to the line number          |





# Datasets 🗂️​
Complete or partial data from the following datasets is included in Fix8:


- **AlMadi2018**: Al Madi, Naser, and Javed Khan. "Constructing semantic networks of comprehension from eye-movement during reading." 2018 IEEE 12th International Conference on Semantic Computing (ICSC). IEEE, 2018.
- **EyeLink_experiment**: Al Madi, Naser, and Javed Khan. "Constructing semantic networks of comprehension from eye-movement during reading." 2018 IEEE 12th International Conference on Semantic Computing (ICSC). IEEE, 2018.
- **EMIP2021**: Bednarik, Roman, et al. "EMIP: The eye movements in programming dataset." Science of Computer Programming 198 (2020): 102520.
- **EMIP2021_90**: Al Madi, Naser, et al. "EMIP Toolkit: A Python Library for Customized Post-processing of the Eye Movements in Programming Dataset." ACM Symposium on Eye Tracking Research and Applications. 2021.
- **Carr2022**: Carr, J. W., Pescuma, V. N., Furlan, M., Ktori, M., & Crepaldi, D. (2022). Algorithms for the automated correction of vertical drift in eye-tracking data. Behavior Research Methods, 54(1), 287-310.
- **GazeBase**: Griffith, H., Lohr, D., Abdulin, E., & Komogortsev, O. (2021). GazeBase, a large-scale, multi-stimulus, longitudinal eye movement dataset. Scientific Data, 8(1), 184.
- **MET_Dataset**: Raymond, O., Moldagali, Y., & Al Madi, N. (2023, May). A dataset of underrepresented languages in eye tracking research. In Proceedings of the 2023 Symposium on Eye Tracking Research and Applications (pp. 1-2).


# API and Documentation for Developers ⚙️
Developers can find the Fix8 Core API documentation [HERE](https://fix8-eye-tracking.github.io/)


# Citation 📝

Naser Al Madi, Brett Torra, Yixin Li, Najam Tariq. (2024). Combining Automation and Expertise: A Semi-automated Approach to Correcting Eye Tracking Data in Reading Tasks.
```bash
@article{Al2024combining,
author = {Naser Al Madi, Brett Torra, Yixin Li, Najam Tariq},
title = {Combining Automation and Expertise: A Semi-automated Approach to Correcting Eye Tracking Data in Reading Tasks},
journal = {},
year = {},
volume = {},
pages = {},
doi = {}
}
```
          
