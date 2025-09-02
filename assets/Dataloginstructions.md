# **Datalog Visualizer – User Guide**

The Datalog Visualizer is an interactive tool for **Datalog queries**. It helps you explore how Datalog rules relate to facts by displaying dependency graphs and letting you examine the data produced by each predicate.

---

## **1. Getting Started**

### **Step 1: Select a Database**

- Use the **dropdown menu** at the top-left to select a database.
- The schema information will appear in the right sidebar.
- This shows you the available tables (EDB predicates) and their attributes.

### **Step 2: Enter a Datalog Query**

- Use the **text input field** below the database dropdown.
- Type a valid Datalog query ending with a dollar sign `$`.
- Click **"Submit"** to generate the dependency graph.
- You can click **"Reset"** to clear everything and start fresh.

**Tip:** See the "Examples" tab in the sidebar for sample queries.

### **Step 3: Explore the Dependency Graph**

- The graph visualizes how predicates depend on each other.
- Use your **mouse or trackpad** to pan and zoom.
- Each node is color-coded by type:
  - **Red nodes**: Answer predicates (query results)
  - **Blue nodes**: IDB predicates (defined by rules)
  - **Green nodes**: EDB predicates (database tables)
  - **Orange diamonds**: Comparison conditions
  - **White circles**: Logical operators (AND, NOT)

---

## **2. Supported Syntax**

### **Basic Datalog Rules**

A Datalog query consists of rules and facts:

- **Rule**: `head :- body.`
- **Fact**: `predicate(constant1, constant2, ...).`
- **Query**: `answer(Variables) :- conditions.`

### **Variables and Constants**

- **Variables**: Start with uppercase letters (X, Y, Name, etc.)
- **Constants**: Can be strings ('John'), numbers (25), or lowercase atoms
- **Anonymous variable**: Use `_` for variables you don't care about

### **Operators**

- **Conjunction**: Use comma `,` for AND
- **Negation**: Use `not` or `~` before a predicate
- **Comparison**: Use `=`, `<>`, `<`, `>`, `<=`, `>=`

### **Query Termination**

- All queries must **end with a dollar sign** `$`

### **Example Query Structure**

```datalog
answer(Name, Salary) :-
    employee(Name, _, _, Salary, _, _, _, _, _, _),
    Salary > 50000.
$
```

---

## **3. Interacting with the Graph**

### **Node Interactions**

- **Click any predicate node** to see its data in the results panel below
- **Click AND nodes** to see explanation of logical conjunction
- **Click NOT nodes** to see explanation of negation
- **Click comparison nodes** to see the condition details

### **Path Highlighting**

- When you click a node, the path from that node down to the base facts (EDB predicates) gets highlighted in red
- This shows the dependency chain and helps trace how data flows through the rules

### **Results Panel**

- Shows the generated SQL query for the selected predicate
- Displays the actual data tuples that satisfy the predicate
- Includes pagination for large result sets
- Shows the total number of tuples found

---

## **4. Understanding Node Types**

### **Answer Nodes (Red)**

- These represent your query results
- The main predicates you're asking about

### **IDB Nodes (Blue)**

- Intensional Database predicates
- Defined by the rules in your query
- Show derived/computed facts

### **EDB Nodes (Green)**

- Extensional Database predicates
- Base facts stored in the database tables
- The foundation data your rules work with

### **Comparison Nodes (Orange Diamonds)**

- Represent conditions like `Salary > 50000`
- Filter the data based on comparisons

### **Logical Operator Nodes (White Circles)**

- **AND nodes**: All connected predicates must be true
- **NOT nodes**: The connected predicate must be false

---

## **5. Using Sample Queries**

The **Examples Tab** (right sidebar) contains useful starter queries:

### **How to Use**

1. Click on a sample query.
2. It will auto-fill the input field.
3. Click **Submit** to generate its dependency graph.
4. Click on nodes to explore the data.

Use these as references to understand common Datalog patterns.

---

## **6. Navigation and Controls**

### **Graph Navigation**

- **Pan**: Click and drag to move around
- **Zoom**: Use mouse wheel or trackpad gestures
- **Reset view**: Double-click empty space

### **Pagination**

- Use **Previous/Next** buttons to navigate through large result sets
- Buttons appear automatically when there are more than 8 results

### **Schema Information**

- Expand/collapse tables in the right sidebar
- See attribute names and data types for each table

---

## **7. Common Questions**

### **Why is my query not working?**

- Make sure your query ends with `$`
- Check that variable names start with uppercase letters
- Verify table and attribute names match the schema

### **Why don't I see any data when I click a node?**

- Make sure you've selected a database first
- Check that the predicate exists in your rules or the database
- Some intermediate nodes (AND, NOT) show explanations instead of data

### **How do I write complex queries?**

- Use the Examples tab for reference patterns
- Start simple and build up complexity gradually
- Remember that Datalog uses logical AND (comma) and NOT operations

---

## **8. Contact & Source Code**

- **Linn Erle Kloefta** – [lklfta1@student.gsu.edu](mailto:lklfta1@student.gsu.edu)
- **Rajshekhar Sunderraman** – [raj@cs.gsu.edu](mailto:raj@cs.gsu.edu)
- **Source Code:** [FormalViz](https://github.com/linnerlek/FormalViz)
