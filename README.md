# MzansiBuilds

A platform for developers to build in public and collaborate.

## Setup

**Requirements:** Python 3.10+

```bash
# Clone the repo
git clone https://github.com/Yaseenobigboi/Derivco_Assessment.git
cd Derivco_Assessment

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac / Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The app will be available at `http://127.0.0.1:5000`.

The database file `mzansibuilds.db` is created automatically on first run.

## Features

- Register and log in with a username and password
- Create a project with a title, description, current stage, and support needed
- Browse the developer feed to see all active projects
- Leave comments on any project
- Send a collaboration request to a project owner
- Track progress with milestones and a progress percentage
- Mark a project as complete
- View completed projects on the Celebration Wall
