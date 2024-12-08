# Academic Chat Bot

This is the README file of our project.

## Basic Project Structure

- frontend
- rag
- data_pipeline
- vector_db
- graph_db

## Dependency Managements

1. Install packages from requirements.txt:
`pip install -r requirements.txt`
2. Write all packages from your current envrionment to requirements.txt:
`pip freeze > requirements.txt`

## Git Branching Modell - Feature Branching

- There are five projects, each housed in its own subfolder to avoid merging conflicts.
- Each team has its own dedicated branch.
- Developers should commit regulary, ensuring that each commit is small and focused on a single topic.
- After completing a feature, teams merge their updates into the main branch.
- Teams should notify others vai MS Teams when they release a new feature that could be important for teams.
- To utilize features developed by other teams, a team should merge these updates into their own branch.

![Branching Strategy Image](./media/branching-model.png)
