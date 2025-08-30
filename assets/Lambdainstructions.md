# **Lambda Engine – User Guide**

Lambda Engine is an interactive visualizer for **Lambda Calculus expressions**. It helps you explore the evaluation process step-by-step by displaying expression trees and letting you apply beta-reductions and arithmetic operations visually.

---

## **1. Getting Started**

### **Step 1: Enter a Lambda Expression**
- Use the **text input field** at the top-left.
- Type a valid lambda calculus expression ending in a semicolon `;`.
- Click **"Submit"** to generate the expression tree.
- You can click **"Reset"** to clear everything and start fresh.

💡 **Tip:** See the "Examples" tab in the sidebar for sample expressions.


### **Step 2: Explore the Expression Tree**
- The tree visualizes the structure of your lambda expression.
- Use your **mouse or trackpad** to pan and zoom.
- Each node is color-coded by type (lambda, apply, operator, variable, number).

You can:
- **Click green "apply" nodes** to perform a beta-reduction.
- **Click arithmetic operator nodes** to evaluate numeric expressions.
- The updated tree is shown automatically after each step.
- At the bottom, the current expression is also displayed as a **string**.

---

## **2. Supported Syntax**

### **Grammar**
A lambda expression must follow this format:

- A variable: `x`, `y`, `a`, etc.
- A number: `5`, `-3`, `2.5`, etc.
- Lambda abstraction: `(lambda x M)`
- Application: `(M N)`
- Arithmetic expression: `(+ M N)`, `(- M N)`, `(* M N)`, `(/ M N)`

All expressions must **end with a semicolon** `;`

### **Examples**
```lisp
(((lambda x (lambda y (+ x y))) 10) 5);
(((lambda f (lambda x (f x))) (lambda y (* y y))) 12);
(lambda f ((lambda x (f (x x)))(lambda x (f (x x)))));
```

---

## **3. Using Sample Expressions**

The **Examples Tab** (right sidebar) contains useful starter expressions:

### **How to Use**
1. Click on a sample.
2. It will auto-fill the input field.
3. Click **Submit** to generate its tree.

Use these as a reference to understand common lambda patterns.

---

## **4. Interacting with the Tree**

- **Apply Node (Green Circle)**: Performs beta-reduction.
- **Operator Node (+, -, *, /)**: Evaluates the arithmetic expression.
- **Lambda Node (Triangle)**: Denotes function definitions.
- **Variable & Number Nodes (Rectangles)**: Leaf elements.

### **Navigation**
- Click the **Back** button to return to a previous state.
- You can explore different reduction paths manually.
- Clicking on other node types will be ignored.

---

## **5. Common Questions**

### **Why does nothing happen when I click a node?**
- Only **green apply nodes** or **arithmetic operator nodes** are clickable.

### **Why is the tree empty?**
- Make sure your expression ends with `;`
- Ensure valid lambda calculus syntax.

### **Can I undo a step?**
- Yes, use the **Back** button to return to any previous tree.

---

## **6. Running the App Locally**

Install dependencies:
```bash
pip install dash igraph networkx ply
```
Or manually install PLY if needed:
- https://www.dabeaz.com/ply/ply-3.11.tar.gz

To run the app:
```bash
python app.py --hostname localhost --port 8081
```
(Default: `localhost:8081`)

---

## **7. Contact & Source Code**
- **Linn Erle Kloefta** – [lklfta1@student.gsu.edu](mailto:lklfta1@student.gsu.edu)
- **Rajshekhar Sunderraman** – [raj@cs.gsu.edu](mailto:raj@cs.gsu.edu)

GitHub Repository: [Lambda Engine](https://github.com/linnerlek/Lambda-Engine)
