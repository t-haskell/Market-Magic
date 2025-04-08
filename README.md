# Market-Magic
Passion machine learning project with a focus on financial markets.

# Reproducible Environment w/ Poetry
All dependencies are handled using Poetry so after cloning this repo simply enter:
'''
poetry install
'''
in the command line. This allows for the backend of the project to be able to be portable and deployed on any environment. 

If IDE does not automatically set the venv as the active environment, the path to interpreter
can be found using:
'''
poetry env info
'''

# Market Magic
An advanced financial market prediction system leveraging Oracle Database, Node.js, Next.js, and Docker.

## Project Goals
- Integrate traditional and alternative market data, employing data preparation techniques
- Predict short-term market movements with simple/intuitive readbility
- Provide scalable deployment options

## Technologies
- **Oracle Database** for relational data storage
- **Node.js** for backend logic
- **Next.js** for frontend UI
- **Docker** for containerized deployments

## Setup Instructions
1. Clone the repository
2. Install dependencies: `npm install`
3. Configure environment variables in `.env` file
4. Run the application: `npm start`
5. Access the app at `http://localhost:3000`
