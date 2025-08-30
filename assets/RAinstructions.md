# **Relational Algebra Visualizer – User Guide**

This tool allows you to **write, visualize, and execute relational algebra queries** interactively. It helps students and database learners understand query execution by displaying expression trees and sub-query results.

---

## **1. Getting Started**
### **Step 1: Select a Database**
- Click the **database dropdown menu** (top-right).
- Select a `.db` file from the available databases.
- Once selected, the database name will appear at the top-left panel.
- The **schema** (list of tables and columns) is displayed on the right.

💡 **Tip:** Ensure your queries match the schema of the selected database.

### **Step 2: Enter a Relational Algebra Query**
- Locate the **query input field** (below the database dropdown).
- Type your relational algebra query using proper syntax (see examples below).
- Click **"Run Query"** to execute.
- To **clear the input**, manually delete or modify the previous query.

💡 **Tip:** Use the **Queries Tab** (right panel) to select sample queries and auto-fill them in the input field.


### **Step 3: Viewing and Interacting with the Visualization**
- The query result appears as a **tree diagram** in the main display area.
- Each **node represents an operation** (e.g., `project`, `select`, `join`).
- Click on **any node** to see its intermediate result in the right panel.
- Use **your mouse or trackpad** to zoom, pan, and adjust the view.



### **Step 4: Exploring Sub-Query Results**
- Clicking a node will highlight it in **red**, indicating selection.
- The right panel displays the corresponding **sub-query output**.
- Expand or resize the right panel to improve visibility.



## **2. Using Pre-Made Queries**
The **Queries Tab** (right panel) contains sample queries for common relational operations.  

### **How to Use Sample Queries**
1. Click on a query in the **Queries Tab**.
2. The query will automatically **populate the input field**.
3. Click **"Run Query"** to execute.

💡 **Tip:** Use these as a reference for writing your own queries.

---

## **3. Supported Operations**
This tool supports the following relational algebra operations:

| **Operation** | **Description** |
|--------------|----------------|
| `project`   | Selects specific columns |
| `select`    | Filters rows based on conditions |
| `join`      | Combines tables using matching columns |
| `rename`    | Renames columns |
| `union`     | Combines results (removes duplicates) |
| `intersect` | Returns common rows between queries |
| `times`     | Computes the Cartesian product |
| `minus`     | Returns rows from the first query not in the second |
| `aggregate` | Performs `SUM`, `AVG`, `COUNT`, `MIN`, `MAX` |

### **Example Queries**
1. **`classroom.db`: Names of buildings which have more than 750 seat capacity in total**
   ```plaintext
   project[bname](aggregate[(bcode, total_seats), (bcode, sum(cap)), (bcode),(sum(cap)>750)](room) join building);
   ```

2. **`company.db`: Employees in departments 1 or 5**
   ```plaintext
   project[fname,lname](select[dno=1](employee))
   union
   project[fname,lname](select[dno=5](employee));
   ```

---

## **4. Common Issues & Solutions**
### **1. Query Not Working?**
- **Check syntax** – Ensure you're using valid relational algebra notation.
- **Verify database schema** – Ensure table and column names match those in the schema.

### **2. Incorrect Results or Empty Output?**
- The database may not contain relevant data for the query.
- Try running a simpler query to check if the data exists.

### **3. Expression Tree Not Displaying?**
- Check for syntax errors before submitting.
- Ensure a database is selected.

---

## **5. Contact & Source Code**
- **For support or questions:**  
  - **Linn Erle Kloefta** – [lklfta1@student.gsu.edu](mailto:lklfta1@student.gsu.edu)
  - **Rajshekhar Sunderraman** - [raj@cs.gsu.edu](mailto:raj@cs.gsu.edu)
- **Source Code:**  
  Available on [GitHub](https://github.com/linnerlek/RA-Viz)
