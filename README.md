# Formal Languages Visualizer
A tool built to help students visualize Formal Languages, currently supports Datalog, Relational Algebra, and Lambda Calculus.

[Try out the hosted program here.](http://tinman.cs.gsu.edu:5021/)

## Running it locally

To run the program locally, Python and Sqlite3 needs to be installed on your local machine.

1. Clone the repository 

    ```bash
    git clone https://github.com/linnerlek/FormalViz.git 
    ```

2. Navigate to the folder

    ```bash
    cd FormalViz
    ```

3. Install the required packages

    ```bash
    pip install -r requirements.txt
    ```

4. Run the program

    ```bash
    python app.py --hostname <optional-host> --port <optional-port>
    ```

    - By default the program runs at `localhost:8050`
    <br>

5. Add your `Sqlite3` database to `databases/`

    - The program comes with sample databases ready for testing.
    <br>

6. Write queries and visualize the data

    - Pre-written queries for the sample databases are available in the sidebar (Examples). 
    - To add your own queries to the docs navigate to `assets/` and add the queries in the relevant file (`RAqueries.md`, `Datalogqueries.md`, or `Lambdaqueries.md`).

## Contact

Reach out to [lklfta1@student.gsu.edu](mailto:lklfta1@student.gsu.edu) if you encounter any problems, or if you have any questions.