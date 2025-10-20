package edu.gsu.cs.drc;

import java.io.*;
import java.util.*;
import java.lang.*;
import edu.gsu.cs.dbengine.*;

public class DRC {

// details of argument, datatype of arguments of predicate node
static public Vector argdetail; 

// list of final free variables to be compared with final limited variables
static public Vector finalfreeVariableMaxConj; 

// list of final limited variables to be compared with final free variables
static public Vector finallimitedVariable;

// list of free variables before recursion to be compared with final limited variables
static public Vector freeVariableMaxConjRecursion; 

// list of limited variables before recursion to be compared with final free variables
static public Vector limitedVariableRecursion;

// list of variables that are used to compare while checking safety rule 3
static public Vector compVariable;

//Public variables required in checkNot() method
static public int flag;
static public int countNot;

//Public variables required in evaluateDRC () method
static public int notOperator;
static public int notOperatorlc;
static public Relation toBeMinuslc;
static public Relation toBeMinus;


static public void main(String argv[]) {
  String dirName = argv[0];
  System.out.print("DRC> ");
  do {
    //Initialize the vectors and variables
    argdetail = new Vector();
    finalfreeVariableMaxConj = new Vector();
    finallimitedVariable = new Vector();
    freeVariableMaxConjRecursion = new Vector();
    limitedVariableRecursion = new Vector();
    compVariable = new Vector();
    flag=0;
    countNot=0;
    notOperator =0;
    notOperatorlc =0;

    String input = readInput().trim();
    if (input.equals("exit"))
      break;
    else
      input = input + "}";
    try {
      StringReader reader = new StringReader(input);
      DRCparser p = new DRCparser(new DRCLexer(reader));
      DRCNode result = (DRCNode) p.parse().value;

      if (result != null) {
      try {
        // Initialize the database
        Relation.initializeDatabase(dirName);

        //Push down NOTs in the tree if NOT is sitting in front of 'or'
        String pushNots = pushNotsDown(result);

        //Perform Name Check, Arity check , Type Check and 
        //Safety rule 2 on the resulted tree
        String semResult = semanticCheck(result);
        if (semResult.equals("OK")) {
          //Perform safety rule 3 (maximal conjuction  of 'and')
          String maxConjAnd = maxConjAndCheck(result);
          if (maxConjAnd.equals("OK")) {
            //perform safety rule 4 (A 'not' operator can only be applied to a 
            //formula if it is connected to a non negated formula with an 'and')
            String checkingNot = checkNot(result);
            if (checkingNot.equals("OK")) {
              Relation answer = evaluateDRC(result);
              answer.setRelationName("ANSWER");
              //System.out.println("\n");
              answer.displayRelationSchema();
              answer.displayRelation();
            }
            else {
              System.out.println("\n SEMANTIC ERROR in DRC Query: "+checkingNot);
            }
          }
          else {
            System.out.println("\n SEMANTIC ERROR in DRC Query: "+maxConjAnd);
          }
        }
        else {
          System.out.println("\n SEMANTIC ERROR in DRC Query: "+semResult);
        }
      } catch (Exception e) {
          System.out.println(e);
          e.printStackTrace();
        }
      }
    } catch (Exception e) {
        System.out.print("Bad Query");
        System.out.print("\n");
      }
  } while (true);
}

//method to push the NOTs down in the tree
static String pushNotsDown(DRCNode tree) {
  Relation r = null;
  if (tree != null) {
    if ((tree.getLchild()==null) && (tree.getRchild()==null)){}
    else if (tree.getRchild()==null) {// unary operator query, exists, forall, not
      if (tree.getRnodetype().equals("not")) {
        DRCNode lc = tree.getLchild();
        String lchildName = (String)lc.getRnodetype();
        if (lchildName.equals("or")) {
          DRCNode orLc=lc.getLchild();
          DRCNode orRc=lc.getRchild();
          tree.setRnodetype("and");
          if (orLc.getRnodetype().equals("not")) {
            DRCNode orLcChild = orLc.getLchild();
            tree.setLchild(orLcChild);
            pushNotsDown(orLcChild);
          }
          else {
            DRCNode newlc = new DRCNode();
            tree.setLchild(newlc);
            newlc.setRnodetype("not");
            newlc.setLchild(orLc);
            pushNotsDown(newlc);
          }
          if (orRc.getRnodetype().equals("not")) {
            DRCNode orRcChild = orRc.getLchild();
            tree.setRchild(orRcChild);
            pushNotsDown(orRcChild);
          }
          else {
            DRCNode newrc = new DRCNode();
            tree.setRchild(newrc);
            newrc.setRnodetype("not");
            newrc.setLchild(orRc);
            pushNotsDown(newrc);
          }
        }
        else { 
          pushNotsDown(lc);
        }
      }
      else { //query, exists, forall
        DRCNode lc = tree.getLchild();
        pushNotsDown(lc);
      }
    }
    else { //and , or
      DRCNode lc = tree.getLchild();
      DRCNode rc = tree.getRchild();
      pushNotsDown(lc);
      pushNotsDown(rc);
    }
  }
  return "OK";
}//end of push NOTs down method

//method to perform Name, Arity, Type and safety check 2
static String semanticCheck(DRCNode tree) {
  Relation r = null;
  if (tree != null) {
    if ((tree.getLchild()==null) && (tree.getRchild()==null)) {
      if (tree.getRnodetype().equals("comp")) {
        Vector freeVariable = new Vector();
        String lopName = (String) tree.leftOperand.get(0);
        String lopDataType = (String) tree.leftDataType.get(0);
        String ropName = (String) tree.rightOperand.get(0);
        String ropDataType = (String) tree.rightDataType.get(0);
        if (lopDataType.equalsIgnoreCase("col")) {
          int ind = argdetail.indexOf(lopName.toUpperCase());
          int indcolumntype = ind + 2;
          String lcolDataType = "";
          if (ind >= 0) {
            lcolDataType = (String) argdetail.get(indcolumntype);
          }
          else
            return "Argument " + lopName + " not found";
          if (ropDataType.equalsIgnoreCase("col")) { // both operands are "col"
            freeVariable.addElement(lopName);
            freeVariable.addElement(ropName);
            ind = argdetail.indexOf(ropName.toUpperCase());
            indcolumntype = ind + 2;
            String rcolDataType = "";
            if (ind >= 0)
              rcolDataType = (String) argdetail.get(indcolumntype);
            else
              return "Argument " + ropName + " not found";
            if (lcolDataType.equals("VARCHAR")) {
              if (!rcolDataType.equals("VARCHAR"))
                return "Mismatch Types: " + lopName + " and " + ropName;
            }
            else {
              if (rcolDataType.equals("VARCHAR"))
                return "Mismatch Types: " + lopName + " and " + ropName;
            }
          }
          else { // lopDataType is "col" and ropDataType is "num" or "str"
            freeVariable.addElement(lopName);
            if ((lcolDataType.equals("VARCHAR") && ropDataType.equals("num")) ||
                (lcolDataType.equals("DECIMAL") && ropDataType.equals("str")) ||
                (lcolDataType.equals("INTEGER") && ropDataType.equals("str")))
              return "Mismatch Types: " + lopName + " and " + ropName;
          }
          tree.setFreeVarList(freeVariable);
        }
      }
      else {
        Vector freeVariable = new Vector();
        String rname = tree.getRelationName().toUpperCase();
        if (Relation.relationExists(rname)) {
          Relation s = Relation.getRelation(rname);
          Vector atts = s.getAttributes();
          int attrsize = atts.size();
          Vector arguments =tree.getArguments();
          Vector temp = new Vector();
          int arg = arguments.size();
          if (attrsize == arg) {
            Vector doms = s.getDomains();
            for (int i=0; i<atts.size(); i++) {
               String domaintype = (String) doms.elementAt(i);
               temp =(Vector) arguments.get(i);
               String attrname= (String) atts.elementAt(i);
               String argname = (String) temp.get(0);
               String datatype = (String) temp.get(1);
               int j=i+1;
               if (datatype.equals("num") || datatype.equals("str")) {
                 if ((domaintype.equals("INTEGER") && datatype.equals("str")) || 
                     (domaintype.equals("DECIMAL") && datatype.equals("str")) ||
                     (domaintype.equals("VARCHAR") && datatype.equals("num")))
                   return "Mismatch Types in ("+j+") argument of relation: " + 
                          rname + " Required Type : "+domaintype+
                          " Available Type: "+datatype ;
               }
               else {
                 freeVariable.addElement(argname);
               }
               argdetail.addElement(argname);
               argdetail.addElement(attrname);
               argdetail.addElement(domaintype);
             }
             tree.setFreeVarList(freeVariable);
           }
           else
             return "Relation "+rname+
                    " does not have same number of columns in query as in Database ";
         }
         else
           return "Relation "+rname+" does not exist";
       }
     }
     else if (tree.getRchild()==null) { // unary operator query,not, exists, forall
               if ((tree.getRnodetype().equals("exists")) || (tree.getRnodetype().equals("forall")))
               {
              Vector freeVariable = new Vector();
              Vector freeVariableChild = new Vector();
              Vector boundVariable = new Vector();
              DRCNode lc = tree.getLchild();
              boundVariable = tree.getVarlist();

              for (int k=0; k<boundVariable.size(); k++)
              {
              String aname1 = (String) boundVariable.get(k);
              for (int g=(k+1); g<boundVariable.size(); g++)
              {
                  String aname2 = (String)boundVariable.get(g);
                  if (aname1.equalsIgnoreCase(aname2))
                         return "multiple Bound variables with same name in FORALL or EXISTS (" + aname1 + ")";
                        }
                     }




              String semStatus = semanticCheck(lc);
              if (semStatus.equalsIgnoreCase("OK"))
              {
               freeVariableChild = lc.getFreeVarList();

              int freeVariableChildSize = freeVariableChild.size();
               for (int i=0; i<freeVariableChildSize; i++)
                {
                  if (boundVariable.contains(freeVariableChild.elementAt(i))){}
                  else
                  freeVariable.addElement(freeVariableChild.elementAt(i));
                }
               tree.setFreeVarList(freeVariable);
              }
              else
              return semStatus;
          }//end of if("exists,forall")
          else  if (tree.getRnodetype().equals("not"))
              {
                Vector freeVariable = new Vector();
                DRCNode lc = tree.getLchild();
                String semStatus = semanticCheck(lc);
                if (semStatus.equalsIgnoreCase("OK"))
                {
                 freeVariable = lc.getFreeVarList();
                tree.setFreeVarList(freeVariable);
                }
                else
                      return semStatus;
              }// end of if ("not")
                else  if (tree.getRnodetype().equals("query"))
                {

              DRCNode lc = tree.getLchild();
              Vector freeVarQuery = tree.getVarlist();
              String semStatus = semanticCheck(lc);
              if (semStatus.equalsIgnoreCase("OK"))
              {
              Vector freeVar = lc.getFreeVarList();
              //System.out.print("\n"+"free variables of children  :"+freeVar+"\n");
              if (freeVar.size() != freeVarQuery.size())
              return "The free variables before '|' in Query "+freeVarQuery+"should be same as free variable after '|' in query "+freeVar;
              else
              {
                for(int i=0; i<freeVar.size();i++)
                {
                  if(freeVarQuery.contains(freeVar.elementAt(i))){}
                  else
                  return "The free variables before '|' in Query "+freeVarQuery+" should be same as free variable after '|' in query "+freeVar;
                }
              }
              }
              else
                  return semStatus;
              }//end of if("query")
      } //end of unary
      else {// and , or
                 if (tree.getRnodetype().equals("and"))
                 {
               Vector freeVariable = new Vector();
               Vector freeVariablelc = new Vector();
               Vector freeVariablerc = new Vector();
                 DRCNode lc = tree.getLchild();
                 DRCNode rc = tree.getRchild();
               String semStatus1 = semanticCheck(lc);
               String semStatus2 = semanticCheck(rc);
               if (semStatus1.equalsIgnoreCase("OK"))
               {
                  if (semStatus2.equalsIgnoreCase("OK"))
                  {

                    freeVariablelc = lc.getFreeVarList();
                    freeVariablerc = rc.getFreeVarList();

                    int freeVariablelcSize =freeVariablelc.size();
                    for (int i=0; i<freeVariablelcSize; i++)
                    freeVariable.addElement(freeVariablelc.elementAt(i));
                    int freeVariablercSize =freeVariablerc.size();
                    int total = freeVariablercSize+freeVariablelcSize;
                    for (int j=0; j<freeVariablercSize; j++)
                    {
                    if (freeVariablelc.contains(freeVariablerc.elementAt(j))){}
                    else
                    freeVariable.addElement(freeVariablerc.elementAt(j));
                     }

                      tree.setFreeVarList(freeVariable);
                  }

                  else
                          return semStatus2;
               }
              else
                      return semStatus1;

                 }
                 else  if (tree.getRnodetype().equals("or"))
                    {
                 Vector freeVariablelc = new Vector();
                   Vector freeVariablerc = new Vector();
                 DRCNode lc = tree.getLchild();
                 DRCNode rc = tree.getRchild();
                 String semStatus1 = semanticCheck(lc);
                 String semStatus2 = semanticCheck(rc);
                 if (semStatus1.equalsIgnoreCase("OK"))
                 {
                    if (semStatus2.equalsIgnoreCase("OK"))
                    {
                      freeVariablelc =lc.getFreeVarList();
                      freeVariablerc =rc.getFreeVarList();
                      int freeVariablelcSize =freeVariablelc.size();
                      int freeVariablercSize =freeVariablerc.size();


                      if(freeVariablelcSize != freeVariablercSize)
                      return "Formulas connected with 'or' does not have same free variables : Left Formula Free variables are "+freeVariablelc+" and Right Formula Free Variables are "+freeVariablerc;
                      else
                      {
                         for (int j=0; j<freeVariablelcSize; j++)
                        {
                          if(((String)(freeVariablelc.elementAt(j))).equals((String)(freeVariablerc.elementAt(j)))){}
                          else
                            return "Formulas connected with 'or' does not have same free variables : Left Formula Free variables are "+freeVariablelc+" and Right Formula Free Variables are "+freeVariablerc;
                        }
                      }


                      tree.setFreeVarList(freeVariablelc);
                    }

                    else
                    return semStatus2;
                 }
                else
                        return semStatus1;

                }
        }

  } // tree is not null
   return "OK";

  } // end of semantic check method




// method to perform safety check 3 (maximal conjuction of 'and')

//Method Working :
static String maxConjAndCheck(DRCNode tree) {

  Relation r = null;

    if (tree != null)
        {
            if ((tree.getLchild()==null) && (tree.getRchild()==null))
            {// comparision and predicate
                 if (tree.getRnodetype().equals("comp"))
                {
                    Vector freeVariableMaxConj = new Vector();
                    Vector limitedVariable = new Vector();
                    String lopName = (String) tree.leftOperand.get(0);
                    String lopDataType = (String) tree.leftDataType.get(0);
                    String ropName = (String) tree.rightOperand.get(0);
                    String ropDataType = (String) tree.rightDataType.get(0);
                    if (lopDataType.equalsIgnoreCase("col"))
                      {
                        if (ropDataType.equalsIgnoreCase("col"))
                          { // both operands are "col"
                               freeVariableMaxConj.addElement(lopName);
                               freeVariableMaxConj.addElement(ropName);
                               limitedVariable = null;
                               compVariable.addElement(lopName);
                               compVariable.addElement(ropName);

                          }
                        else
                          { // lopDataType is "col" and ropDataType is "num" or "str"
                             freeVariableMaxConj.addElement(lopName);
                             limitedVariable.addElement(lopName);
                          }
                        tree.setFreeVarListMaxConj(freeVariableMaxConj);
                        tree.setLimitedVarList(limitedVariable);

                      }
                }
                else //predicate
                {
                  Vector freeVariableMaxConj = new Vector();
                  Vector arguments =tree.getArguments();
                  Vector temp = new Vector();
                  int arg = arguments.size();
                  for (int i=0; i<arguments.size(); i++)
                    {
                      temp =(Vector) arguments.get(i);
                      String argname = (String) temp.get(0);
                      String datatype = (String) temp.get(1);
                      if(datatype.equals("col"))
                      {
                      freeVariableMaxConj.addElement(argname);
                      }
                     }
                  tree.setFreeVarListMaxConj(freeVariableMaxConj);

                  tree.setLimitedVarList(freeVariableMaxConj);
                }
            }
            else if (tree.getRchild()==null)
            { // unary operator query, exists, forall, not
                if (tree.getRnodetype().equals("not"))
                  {
                  Vector limitedVariable = new Vector();
                  DRCNode lc = tree.getLchild();
                  String maxConjAnd = maxConjAndCheck(lc);
                  if (maxConjAnd.equalsIgnoreCase("OK"))
                  {
                    if(lc.getRnodetype().equals("predicate"))
                    {
                      tree.setFreeVarListMaxConj(lc.getFreeVarListMaxConj());
                      limitedVariable =null;
                      tree.setLimitedVarList(limitedVariable);
                    }
                    else if (lc.getRnodetype().equals("exists"))
                    {
                            Vector boundVariable = new Vector();
                          boundVariable = lc.getVarlist();
                          DRCNode lcChild = lc.getLchild();
                          String maxConjAndch= maxConjAndCheck(lcChild );
                        if (maxConjAndch.equalsIgnoreCase("OK"))
                          {

                          Vector freeVar = lcChild.getFreeVarList();
                          Vector ltdVar= lcChild.getLimitedVarList();
                          Vector newFreeVar = new Vector();

                          int freeVariableSize = freeVar.size();


                           for (int i=0; i<freeVariableSize; i++)
                            {

                              if (boundVariable.contains(freeVar.elementAt(i)))
                              {

                                if(ltdVar != null)
                                {

                                 if(ltdVar.contains(freeVar.elementAt(i)))
                                 {

                                 }
                                 else
                                 ltdVar.addElement(freeVar.elementAt(i));
                                }
                                else
                                {

                                  Vector ltdVartemp = new Vector();
                                  ltdVartemp.addElement(freeVar.elementAt(i));
                                  ltdVar = ltdVartemp;

                                }
                              }
                              else
                              {
                               newFreeVar.addElement(freeVar.elementAt(i));

                              }
                            }

                            for (int j=0; j<newFreeVar.size(); j++)
                            {
                              if(newFreeVar != null)
                              {
                                if(ltdVar.contains(newFreeVar.elementAt(j)))
                                 {
                                   ltdVar.remove(newFreeVar.elementAt(j));
                                 }

                              }


                            }


                          tree.setFreeVarListMaxConj(newFreeVar);

                            tree.setLimitedVarList(ltdVar);
                        }
                         else
                         return maxConjAndch;


                    }
                    else
                    {

                      tree.setFreeVarListMaxConj(lc.getFreeVarListMaxConj());
                      tree.setLimitedVarList(lc.getLimitedVarList());


                    }
                  }
                  else
                    return maxConjAnd;

                  }
                  else if (tree.getRnodetype().equals("exists")) // exists
                  {
                    Vector boundVariable = new Vector();
                    Vector limitedVariable = new Vector();
                    boundVariable = tree.getVarlist();
                    DRCNode lc = tree.getLchild();
                    String maxConjAnd = maxConjAndCheck(lc);



                  if (maxConjAnd.equalsIgnoreCase("OK"))
                    {
                     boundVariable = tree.getVarlist();

                    Vector freeVarChild = lc.getFreeVarList();
                    Vector ltdVarChild = lc.getLimitedVarList();
                    Vector newFreeVar = new Vector();

                    int freeVariableChildSize = freeVarChild.size();


                           for (int i=0; i<freeVariableChildSize; i++)
                            {

                              if (boundVariable.contains(freeVarChild.elementAt(i)))
                              {

                                if(ltdVarChild != null)
                                {

                                 if(ltdVarChild.contains(freeVarChild.elementAt(i)))
                                 {

                                 }
                                 else
                                 ltdVarChild.addElement(freeVarChild.elementAt(i));
                                }
                                else
                                {

                                  Vector ltdVarChildtemp = new Vector();
                                  ltdVarChildtemp.addElement(freeVarChild.elementAt(i));
                                  ltdVarChild = ltdVarChildtemp;

                                }
                              }
                              else {}

                            }


                           tree.setFreeVarListMaxConj(freeVarChild);
                           tree.setLimitedVarList(ltdVarChild);


                   }
                    else
                    return maxConjAnd;


                  }
                  else //query
                  {
                      DRCNode lc = tree.getLchild();
                    String maxConjAnd = maxConjAndCheck(lc);
                    if (maxConjAnd.equalsIgnoreCase("OK"))
                    {

                     tree.setFreeVarListMaxConj(lc.getFreeVarListMaxConj());
                     tree.setLimitedVarList(lc.getLimitedVarList());

                    }
                    else
                    return maxConjAnd;
                  }

              }
              else
              {// and , or
                if (tree.getRnodetype().equals("or"))
                    {
                DRCNode lc = tree.getLchild();
                DRCNode rc = tree.getRchild();
                Vector freeVariableMaxConj = new Vector();
                Vector limitedVariable = new Vector();

                String maxConjAnd1 = maxConjAndCheck(lc);
                    String maxConjAnd2 = maxConjAndCheck(rc);

                if (maxConjAnd1.equalsIgnoreCase("OK"))
                {

                  if (maxConjAnd2.equalsIgnoreCase("OK"))
                  {

                  }
                  else
                  return maxConjAnd2;
                }else
                return maxConjAnd1;
              }
            else if (tree.getRnodetype().equals("and"))
              {
                 Vector freeVariableMaxConj = new Vector();
                 Vector limitedVariable = new Vector();

                // get the left and right child  of 'and' node
                 DRCNode lc = tree.getLchild();
                 DRCNode rc = tree.getRchild();



                   // if the right child of 'and' node is also 'and' (conjuction of 'and')
                   if(rc.getRnodetype().equals("and"))
                   {

                      // collect the free and limited variables of left child and store them in final free and limited var list
                         maxConjAndCheck(lc);
                      freeVariableMaxConj = lc.getFreeVarListMaxConj();
                      limitedVariable = lc.getLimitedVarList();

                      int freeVariableMaxConjSize =freeVariableMaxConj.size();
                      for (int i=0; i<freeVariableMaxConjSize; i++)
                      {
                        if(finalfreeVariableMaxConj.contains(freeVariableMaxConj.elementAt(i))){}
                        else
                        finalfreeVariableMaxConj.addElement(freeVariableMaxConj.elementAt(i));
                      }


                      if (limitedVariable == null) {}
                      else
                      {
                        for (int i=0; i<limitedVariable.size(); i++)
                        {
                        if(finallimitedVariable.contains(limitedVariable.elementAt(i))){}
                        else
                        finallimitedVariable.addElement(limitedVariable.elementAt(i));
                        }
                      }


                      // apply the same method maxConjAndCheck() to right child
                      String maxConjAnd = maxConjAndCheck(rc);
                      if (maxConjAnd.equalsIgnoreCase("OK")){}
                      else
                         return maxConjAnd;


                   }
                   else // case when the right child of 'and' node is not 'and' ( end of the maximal conjuction of 'and')
                   {
                     Vector freeVariableMaxConjlc= new Vector();
                     Vector limitedVariablelc = new Vector();
                     Vector freeVariableMaxConjrc= new Vector();
                     Vector limitedVariablerc = new Vector();


                    // if the right child of 'and' is 'not', 'or' , 'exists' (possible case of recursive maximal conjuction of 'and')
                    if(rc.getRnodetype().equals("not") || rc.getRnodetype().equals("or") ||rc.getRnodetype().equals("exists"))
                    {
                            //////////changed nov 8/////////////
                            DRCNode rcRcChild = rc.getLchild();
                            String maxConjAndRC = maxConjAndCheck(rcRcChild);
                            if (maxConjAndRC.equalsIgnoreCase("OK")){}
                            else{return maxConjAndRC;}
                            ////////////////////////////////////////

                            String maxConjAnd1 = maxConjAndCheck(lc);

                            if (maxConjAnd1.equalsIgnoreCase("OK"))
                            {
                              freeVariableMaxConjlc = lc.getFreeVarListMaxConj();

                              limitedVariablelc = lc.getLimitedVarList();
                            }
                            else
                            return maxConjAnd1;


                            for (int i=0; i<freeVariableMaxConjlc.size(); i++)
                             {
                             if(finalfreeVariableMaxConj.contains(freeVariableMaxConjlc.elementAt(i))){}
                             else
                             finalfreeVariableMaxConj.addElement(freeVariableMaxConjlc.elementAt(i));
                             }

                            if (limitedVariablelc == null) {}
                            else
                              {
                               for (int i=0; i<limitedVariablelc.size(); i++)
                               {
                               if(finallimitedVariable.contains(limitedVariablelc.elementAt(i))){}
                               else
                                finallimitedVariable.addElement(limitedVariablelc.elementAt(i));
                                }
                              }



                            // store all the free variables and limited variables till this point
                            for (int i=0; i<finalfreeVariableMaxConj.size(); i++)
                             if(freeVariableMaxConjRecursion.contains(finalfreeVariableMaxConj.elementAt(i))){}
                             else
                              freeVariableMaxConjRecursion.addElement(finalfreeVariableMaxConj.elementAt(i));





                            if (finallimitedVariable == null) {}
                            else
                            {
                              for (int i=0; i<finallimitedVariable.size(); i++)
                              limitedVariableRecursion.addElement(finallimitedVariable.elementAt(i));
                            }




                            finalfreeVariableMaxConj =  new Vector();
                            finallimitedVariable =  new Vector();

                                //DRCNode rcRcChild = rc.getLchild();
                              //String maxConjAndRC = maxConjAndCheck(rcRcChild);

                              //if (maxConjAndRC.equalsIgnoreCase("OK")){}
                              //else{return maxConjAndRC;}






                          //check if 'not' node or 'exists' node has child that is either predicate or comparision type
                            if(rc.getRnodetype().equals("not") || rc.getRnodetype().equals("exists"))
                            {
                               DRCNode lcNotOrExists = rc.getLchild();
                               if(lcNotOrExists.getRnodetype().equals("comp")||lcNotOrExists.getRnodetype().equals("predicate"))
                               {
                                 String maxConjAnd = maxConjAndCheck(lcNotOrExists);
                                 freeVariableMaxConjrc = lcNotOrExists.getFreeVarListMaxConj();
                                 if(rc.getRnodetype().equals("not"))
                                 limitedVariablerc = null;
                                 else
                                 limitedVariablerc = lcNotOrExists.getLimitedVarList();
                               }
                               else
                               {
                                    String maxConjAnd2 = maxConjAndCheck(rc);
                                    if (maxConjAnd2.equalsIgnoreCase("OK"))
                                    {

                                      freeVariableMaxConjrc = rc.getFreeVarListMaxConj();
                                      limitedVariablerc = rc.getLimitedVarList();


                                      for (int i=0; i<freeVariableMaxConjrc.size(); i++)
                                       {
                                       if(finalfreeVariableMaxConj.contains(freeVariableMaxConjrc.elementAt(i))){}
                                       else
                                       finalfreeVariableMaxConj.addElement(freeVariableMaxConjrc.elementAt(i));
                                       }

                                      if (limitedVariablerc == null) {}
                                      else
                                        {
                                         for (int i=0; i<limitedVariablerc.size(); i++)
                                         {
                                         if(finallimitedVariable.contains(limitedVariablerc.elementAt(i))){}
                                         else
                                          finallimitedVariable.addElement(limitedVariablerc.elementAt(i));
                                          }
                                      }


                                      for (int i=0; i<finalfreeVariableMaxConj.size(); i++)
                                      {

                                        if(freeVariableMaxConjrc.contains(finalfreeVariableMaxConj.elementAt(i))){}
                                        else
                                        freeVariableMaxConjrc.addElement(finalfreeVariableMaxConj.elementAt(i));
                                      }


                                      if (limitedVariablerc == null) {}
                                      else
                                      {
                                        for (int i=0; i<finallimitedVariable.size(); i++)
                                        {

                                          if(limitedVariablerc.contains(finallimitedVariable.elementAt(i))){}
                                           else
                                          limitedVariablerc.addElement(finallimitedVariable.elementAt(i));
                                        }
                                      }


                                        for (int i=0; i<freeVariableMaxConjRecursion.size(); i++)
                                         {
                                           if(finalfreeVariableMaxConj.contains(freeVariableMaxConjRecursion.elementAt(i))){}
                                           else
                                          finalfreeVariableMaxConj.addElement(freeVariableMaxConjRecursion.elementAt(i));
                                        }

                                        if (limitedVariableRecursion == null) {}
                                        else
                                        {
                                          for (int i=0; i<limitedVariableRecursion.size(); i++)
                                          {
                                            if(finallimitedVariable.contains(limitedVariableRecursion.elementAt(i))){}
                                             else
                                            finallimitedVariable.addElement(limitedVariableRecursion.elementAt(i));
                                          }
                                        }
                                    }
                                    else
                                    return maxConjAnd2;
                                  }


                            }

                            // if rc node type is 'or'
                            else
                            {
                                String maxConjAnd2 = maxConjAndCheck(rc);
                                if (maxConjAnd2.equalsIgnoreCase("OK"))
                                {

                                  freeVariableMaxConjrc = rc.getFreeVarListMaxConj();
                                  limitedVariablerc = rc.getLimitedVarList();


                                  for (int i=0; i<freeVariableMaxConjrc.size(); i++)
                                   {
                                   if(finalfreeVariableMaxConj.contains(freeVariableMaxConjrc.elementAt(i))){}
                                   else
                                   finalfreeVariableMaxConj.addElement(freeVariableMaxConjrc.elementAt(i));
                                   }

                                  if (limitedVariablerc == null) {}
                                  else
                                    {
                                     for (int i=0; i<limitedVariablerc.size(); i++)
                                     {
                                     if(finallimitedVariable.contains(limitedVariablerc.elementAt(i))){}
                                     else
                                      finallimitedVariable.addElement(limitedVariablerc.elementAt(i));
                                      }
                                  }


                                  for (int i=0; i<finalfreeVariableMaxConj.size(); i++)
                                  {

                                    if(freeVariableMaxConjrc.contains(finalfreeVariableMaxConj.elementAt(i))){}
                                    else
                                    freeVariableMaxConjrc.addElement(finalfreeVariableMaxConj.elementAt(i));
                                  }


                                  if (limitedVariablerc == null) {}
                                  else
                                  {
                                    for (int i=0; i<finallimitedVariable.size(); i++)
                                    {

                                      if(limitedVariablerc.contains(finallimitedVariable.elementAt(i))){}
                                       else
                                      limitedVariablerc.addElement(finallimitedVariable.elementAt(i));
                                    }
                                  }


                                    for (int i=0; i<freeVariableMaxConjRecursion.size(); i++)
                                     {
                                       if(finalfreeVariableMaxConj.contains(freeVariableMaxConjRecursion.elementAt(i))){}
                                       else
                                      finalfreeVariableMaxConj.addElement(freeVariableMaxConjRecursion.elementAt(i));
                                    }

                                    if (limitedVariableRecursion == null) {}
                                    else
                                    {
                                      for (int i=0; i<limitedVariableRecursion.size(); i++)
                                      {
                                        if(finallimitedVariable.contains(limitedVariableRecursion.elementAt(i))){}
                                         else
                                        finallimitedVariable.addElement(limitedVariableRecursion.elementAt(i));
                                      }
                                    }
                                }
                                else
                                return maxConjAnd2;
                              }



                    }

                    // if right child of 'and' is either 'predicate' or 'comparision' type ( end of the maximal conjuction of 'and' )
                    else if (rc.getRnodetype().equals("comp") || rc.getRnodetype().equals("predicate"))
                    {

                         String maxConjAnd1 = maxConjAndCheck(lc);
                      String maxConjAnd2 = maxConjAndCheck(rc);

                      if (maxConjAnd1.equalsIgnoreCase("OK"))
                      {
                        freeVariableMaxConjlc = lc.getFreeVarListMaxConj();
                        limitedVariablelc = lc.getLimitedVarList();

                        if (maxConjAnd2.equalsIgnoreCase("OK")){
                          freeVariableMaxConjrc = rc.getFreeVarListMaxConj();
                          limitedVariablerc = rc.getLimitedVarList();}
                        else
                        return maxConjAnd2;
                      }else
                      return maxConjAnd1;

                    }



                     for (int i=0; i<freeVariableMaxConjlc.size(); i++)
                     {
                     if(finalfreeVariableMaxConj.contains(freeVariableMaxConjlc.elementAt(i))){}
                     else
                     finalfreeVariableMaxConj.addElement(freeVariableMaxConjlc.elementAt(i));
                     }

                    if (limitedVariablelc == null) {}
                    else
                      {
                       for (int i=0; i<limitedVariablelc.size(); i++)
                       {
                       if(finallimitedVariable.contains(limitedVariablelc.elementAt(i))){}
                       else
                        finallimitedVariable.addElement(limitedVariablelc.elementAt(i));
                        }
                       }


                     for (int i=0; i<freeVariableMaxConjrc.size(); i++)
                     {
                      if(finalfreeVariableMaxConj.contains(freeVariableMaxConjrc.elementAt(i))){}
                      else
                      finalfreeVariableMaxConj.addElement(freeVariableMaxConjrc.elementAt(i));
                      }


                    if (limitedVariablerc == null) {}
                    else
                      {
                       for (int i=0; i<limitedVariablerc.size(); i++)
                       {
                       if(finallimitedVariable.contains(limitedVariablerc.elementAt(i))){}
                       else
                       finallimitedVariable.addElement(limitedVariablerc.elementAt(i));
                       }
                      }


                       int compVariableSize = compVariable.size();

                       for (int i=0; i<compVariableSize; i=i+2)
                       {
                        if(finallimitedVariable.contains(compVariable.elementAt(i)))
                        {  if(finallimitedVariable.contains(compVariable.elementAt(i+1))){}
                          else
                          finallimitedVariable.addElement(compVariable.elementAt(i+1));
                        }
                        else if (finallimitedVariable.contains(compVariable.elementAt(i+1)))
                        {
                          if(finallimitedVariable.contains(compVariable.elementAt(i))){}
                          else
                          finallimitedVariable.addElement(compVariable.elementAt(i));
                        }
                       }

                      // Vector to store the variable list that are found not limited
                      Vector notLimitedVar = new Vector();


                      for (int j=0; j<finalfreeVariableMaxConj.size(); j++)
                      {
                        if (finallimitedVariable.contains(finalfreeVariableMaxConj.elementAt(j))){}
                        else
                        {
                          notLimitedVar.addElement(finalfreeVariableMaxConj.elementAt(j));
                        }

                      }


                      if( notLimitedVar.size() !=0)
                      return "The free variable " +notLimitedVar+" is not limited hence violating rule # 3 of Safe DRC formula";
                  }
                  tree.setLimitedVarList(finallimitedVariable);
              }
              }
      }
    return "OK";
  }// end of maximal conjuction of 'and' method



  // method to perform safety check 4 : A 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'
  static String checkNot(DRCNode tree)
        {

            if (tree != null)
              {
               if ((tree.getLchild()==null) && (tree.getRchild()==null)){}
               else if (tree.getRchild()==null)
               { // unary operator query, exists, forall, not
                 if (tree.getRnodetype().equals("not"))
                 {
                  return "rule # 4  of Safe DRC formula is violated : A 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'";
                }
                else
                { //query, exists, forall
                 DRCNode lc = tree.getLchild();
                 String checkingNot = checkNot(lc);
                 if (checkingNot.equalsIgnoreCase("OK"))
                  {}
                 else
                  return checkingNot;
                 }
                }
                else { //and , or

                   DRCNode lc = tree.getLchild();
                     DRCNode rc = tree.getRchild();

                   if (tree.getRnodetype().equals("or"))
                   {
                    if (lc.getRnodetype().equals("not") || rc.getRnodetype().equals("not"))
                     {
                      return "rule # 4 of Safe DRC formula is violated : A 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'";
                    }
                    else
                    {
                       String checkingNot1 = checkNot(lc);
                       if (checkingNot1.equalsIgnoreCase("OK"))
                       {
                         String checkingNot2 = checkNot(rc);
                         if (checkingNot2.equalsIgnoreCase("OK")){}
                         else
                         return checkingNot2;

                       }
                       else
                         return checkingNot1;

                    }
                  }
                  else if (tree.getRnodetype().equals("and"))
                  {
                    if (lc.getRnodetype().equals("not")){countNot++;}
                    else
                    flag =1;
                    if(rc.getRnodetype().equals("and"))
                     {

                      String checkingNot2 = checkNot(rc);
                       if (checkingNot2.equalsIgnoreCase("OK")){}
                       else
                       return checkingNot2;
                    }
                    else
                    {
                      if(rc.getRnodetype().equals("not"))
                      {
                        if (flag==1)
                        {
                          DRCNode lcNot = rc.getLchild();
                          flag =0;
                            countNot=0;
                          String checkingNot2 = checkNot(lcNot);
                          if (checkingNot2.equalsIgnoreCase("OK")){}
                           else
                           return checkingNot2;
                        }
                        else
                        return "rule # 4 of Safe DRC formula is violated : A 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'";
                      }
                      else
                      {
                        flag=1;
                        if(countNot!=0 && flag==0)
                        return "rule # 4 of Safe DRC formula is violated : A 'not' operator can only be applied to a formula if it is connected to a non negated formula with an 'and'";
                        else
                        {
                        flag =0;
                        countNot=0;
                        String checkingNot2 = checkNot(rc);
                         if (checkingNot2.equalsIgnoreCase("OK")){}
                         else
                         return checkingNot2;
                        }
                      }



                    }


                  }


                     }
             }
          return "OK";
      }// end of safety rule 4 check method



  // method to evalute DRC Query by converting into RA
  static Relation evaluateDRC(DRCNode tree)
  {
    if (tree != null) {
      if ((tree.getLchild()==null) && (tree.getRchild()==null)) //comparision , predicate
             {
              if (tree.getRnodetype().equals("comp"))
                 {

                  Vector compVarEvalDRC = new Vector();
                  String lopName = (String) tree.leftOperand.get(0);
                  String lopDataType = (String) tree.leftDataType.get(0);
                  String compOp = (String) tree.operator.get(0);
                  String ropName = (String) tree.rightOperand.get(0);
                  String ropDataType = (String) tree.rightDataType.get(0);

                 compVarEvalDRC.addElement(lopDataType);
                 compVarEvalDRC.addElement(lopName);
                 compVarEvalDRC.addElement(compOp);
                 compVarEvalDRC.addElement(ropDataType);
                 compVarEvalDRC.addElement(ropName);

                 tree.setSelectionVarList(compVarEvalDRC);





              }
                 else
                    {


                String[] varName = new String[50];
                Vector varVal = new Vector();

                String rname = tree.getRelationName().toUpperCase();
                Relation answer =  Relation.getRelation(rname);
                Vector arguments =tree.getArguments();
                Vector temp = new Vector();
                Vector rnames = new Vector();
                Vector rtype = new Vector();
                Vector renamedArg = new Vector();
                Vector argNotConstant = new Vector();
                Vector argRenameBack = new Vector();
                Vector varvalue = new Vector();

                for (int j=0; j<arguments.size(); j++)
                   {

                    temp =(Vector) arguments.get(j);
                    String argname = (String) temp.get(0);
                    String datatype = (String) temp.get(1);
                    rnames.addElement(argname);
                    rtype.addElement(datatype);

                    //System.out.print("Before filling variable vecor");
                    String temporary = Integer.toString(j);
                    varName[j] = "X_"+ temporary;
                    varvalue.addElement(argname);
                    renamedArg.addElement(varName[j]);
                  }
                  varVal= varvalue;


                if(rtype.contains("str") || rtype.contains("num"))
                {

                  answer = answer.rename(renamedArg);
                  for(int i=0; i<arguments.size(); i++)
                  {
                    if(rtype.elementAt(i).equals("str") || rtype.elementAt(i).equals("num"))
                    {
                      String lDataType = "col";
                      String lName = (String) varName[i];
                      String cmpOp = "=";
                      String rDataType = (String) rtype.elementAt(i);
                      String rName = (String) rnames.elementAt(i);
                      answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                    }
                    else
                    {
                      argNotConstant.addElement(renamedArg.elementAt(i));
                    }

                  }


                  for(int m=0; m<renamedArg.size(); m++)
                  {
                    if(argNotConstant.contains((String) renamedArg.elementAt(m)))
                      {

                        for(int j=0; j<renamedArg.size(); j++)
                        {

                            if(((String) varvalue.elementAt(m)).equals((String) varvalue.elementAt(j)) && m!=j)
                              {
                                String lDataType = "col";
                                String lName = (String) varName[m];
                                String cmpOp = "=";
                                String rDataType = "col";
                                String rName = (String) varName[j];
                                answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                argNotConstant.remove(renamedArg.elementAt(j));
                              }


                        }
                      }
                      else{}
                      //System.out.print("argNotConstant not contains: "+ renamedArg.elementAt(m)+"\n");
                  }



                  answer = answer.projection(argNotConstant);

                  for(int j=0; j<argNotConstant.size(); j++)
                  {
                    int index =renamedArg.indexOf(argNotConstant.elementAt(j));
                    argRenameBack.addElement(rnames.elementAt(index));
                  }

                  answer = answer.rename(argRenameBack);

                }
                else
                {
                  answer = answer.rename(renamedArg);
                  for(int i=0; i<arguments.size(); i++)
                  {
                    argNotConstant.addElement(renamedArg.elementAt(i));
                  }

                  for(int m=0; m<renamedArg.size(); m++)
                  {
                    if(argNotConstant.contains((String) renamedArg.elementAt(m)))
                      {

                        for(int j=0; j<renamedArg.size(); j++)
                        {

                            if(((String) varvalue.elementAt(m)).equals((String) varvalue.elementAt(j)) && m!=j)
                              {
                                String lDataType = "col";
                                String lName = (String) varName[m];
                                String cmpOp = "=";
                                String rDataType = "col";
                                String rName = (String) varName[j];
                                answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                argNotConstant.remove(renamedArg.elementAt(j));
                              }


                        }
                      }
                      else{}

                  }


                  answer = answer.projection(argNotConstant);

                  for(int j=0; j<argNotConstant.size(); j++)
                  {
                    int index =renamedArg.indexOf(argNotConstant.elementAt(j));
                    argRenameBack.addElement(rnames.elementAt(index));
                  }

                  answer = answer.rename(argRenameBack);
                }


                       return answer;

              }

            }
      else if (tree.getRchild()==null)  // unary operator query, exists, not
            {
             if (tree.getRnodetype().equals("query"))
               {


                DRCNode lc = tree.getLchild();
                if( lc.getRnodetype().equals("and"))
                   {
                        Relation lcRel = evaluateDRC(lc);
                        Vector boundVarExists = tree.getVarlist();

                        if(notOperator > 0)
                        {
                            Vector vartoBeMinus= new Vector();
                            Vector varToBeMinuslc= new Vector();
                            Relation lcRelTemp = lcRel;
                            Relation answer = new Relation(null,null,null);

                            if(toBeMinus != null)
                            {
                              vartoBeMinus = toBeMinus.getAttributes();
                              lcRel = lcRel.projection(vartoBeMinus);
                              answer = lcRel.minus(toBeMinus);

                              answer = answer.projection(boundVarExists);
                              notOperator --;
                                Relation toBeMinus = new Relation(null,null,null);
                                if(notOperatorlc>0)
                                {
                                  if(toBeMinuslc != null)
                                  {
                                      varToBeMinuslc = toBeMinuslc.getAttributes();
                                      Vector tempAnswer = answer.getAttributes();
                                      Relation tempAns = answer;
                                      answer = answer.projection(varToBeMinuslc);
                                      Relation temporary = answer.minus(toBeMinuslc);
                                       answer = temporary;
                                         temporary = new Relation(null,null,null);
                                         answer = answer.projection(boundVarExists);
                                         notOperatorlc--;
                                           Relation toBeMinuslc = new Relation(null,null,null);
                                      }
                                }


                            }
                            else
                            {answer = lcRel;}


                            return answer;
                        }
                        else
                        {
                          Relation answer = new Relation(null,null,null);
                          if(notOperatorlc>0)
                          {
                            Vector vartoBeMinus= new Vector();
                            Vector varToBeMinuslc= new Vector();
                            Relation lcRelTemp = lcRel;

                            if(toBeMinuslc != null)
                            {
                                varToBeMinuslc = toBeMinuslc.getAttributes();
                                Vector tempAnswer = answer.getAttributes();
                                Relation tempAns = answer;
                                answer = lcRel.projection(varToBeMinuslc);
                                Relation
                                temporary = answer.minus(toBeMinuslc);
                                 answer = temporary;
                                 temporary = new Relation(null,null,null);
                                 answer = answer.projection(boundVarExists);
                                 notOperatorlc--;
                                 Relation toBeMinuslc = new Relation(null,null,null);
                            }

                          }
                          else
                          {
                            lcRel = lcRel.projection(boundVarExists);
                            answer = lcRel;
                          }
                          return answer;
                        }
                    }

                else
                  {
                    Relation lcRel = evaluateDRC(lc);
                    Vector QueryVarList = tree.getVarlist();
                    Relation answer = lcRel.projection(QueryVarList);
                    return answer;
                  }
              }
             else if ((tree.getRnodetype().equals("not")))
               {
                DRCNode lc = tree.getLchild();
                Relation answer = evaluateDRC(lc);
                notOperator++;
                return answer;

               }
             else
               {

                 DRCNode lc = tree.getLchild();
                 if( lc.getRnodetype().equals("and"))
                 {

                   Relation lcRel = evaluateDRC(lc);

                  if(notOperator > 0)
                  {


                    Vector boundVarExists = tree.getVarlist();
                    Vector freeVariableChild = lcRel.getAttributes();

                    Vector temp = new Vector();

                    for(int i=0; i<freeVariableChild.size();i++)
                    {
                      if(boundVarExists.contains(freeVariableChild.elementAt(i))){}
                      else
                      temp.addElement(freeVariableChild.elementAt(i));
                    }

                    if(boundVarExists.size() == freeVariableChild.size()){Relation answer = lcRel;return answer;}


                    else
                    {
                      Vector vartoBeMinus= new Vector();
                      Vector varToBeMinuslc= new Vector();
                      Relation lcRelTemp = lcRel;

                      Relation answer = new Relation(null,null,null);
                      Relation temporary = new Relation(null,null,null);

                      if(toBeMinus != null)
                      {
                          vartoBeMinus = toBeMinus.getAttributes();
                          lcRel = lcRel.projection(vartoBeMinus);

                          temporary = lcRel.minus(toBeMinus);
                          answer = temporary;

                          temporary = new Relation(null,null,null);
                          int x=0;

                          if(temp != null && vartoBeMinus!= null)
                          {
                            for(int v=0; v<temp.size(); v++)
                            {
                            if(vartoBeMinus.contains(temp.elementAt(v))){}
                            else
                            x=1;

                            }
                          }

                          if(temp != null && vartoBeMinus!= null && temp.size()<= vartoBeMinus.size() && x!=1)
                          {
                            answer = answer.projection(temp);

                          }

                          else
                          {
                            answer = answer.join(lcRelTemp);
                            answer = answer.projection(temp);

                          }

                            notOperator--;
                             Relation toBeMinus = new Relation(null,null,null);

                             if(notOperatorlc>0)
                              {
                                if(toBeMinuslc != null)
                                {
                                    varToBeMinuslc = toBeMinuslc.getAttributes();
                                    Vector tempAnswer = answer.getAttributes();
                                    Relation tempAns = answer;
                                    answer = answer.projection(varToBeMinuslc);
                                    temporary = answer.minus(toBeMinuslc);

                                     answer = temporary;
                                     temporary = new Relation(null,null,null);
                                     x=0;

                                      if(tempAnswer != null && varToBeMinuslc!= null)
                                      {
                                        for(int v=0; v<tempAnswer.size(); v++)
                                        {
                                        if(varToBeMinuslc.contains(tempAnswer.elementAt(v))){}
                                        else
                                        x=1;

                                        }
                                      }

                                    if(tempAnswer != null && varToBeMinuslc!= null && tempAnswer.size()<= varToBeMinuslc.size() && x!=1)
                                    {
                                      answer = answer.projection(tempAnswer);

                                    }

                                    else
                                    {
                                      answer = answer.join(tempAns);
                                      answer = answer.projection(tempAnswer);

                                    }


                                    notOperatorlc--;
                                    Relation toBeMinuslc = new Relation(null,null,null);



                                 }
                                else
                                answer = lcRel;


                              }
                      }
                      else
                      {
                        answer = lcRel;
                        if(notOperatorlc>0)
                              {
                                if(toBeMinuslc != null)
                                {
                                    varToBeMinuslc = toBeMinuslc.getAttributes();
                                    answer = answer.projection(varToBeMinuslc);
                                    temporary = answer.minus(toBeMinuslc);
                                     answer = temporary;
                                     temporary = new Relation(null,null,null);
                                     int x=0;

                                      if(temp != null && varToBeMinuslc!= null)
                                      {
                                        for(int v=0; v<temp.size(); v++)
                                        {
                                        if(varToBeMinuslc.contains(temp.elementAt(v))){}
                                        else
                                        x=1;

                                        }
                                      }

                                    if(temp != null && varToBeMinuslc!= null && temp.size()<= varToBeMinuslc.size() && x!=1)
                                    {
                                      answer = answer.projection(temp);

                                    }

                                    else
                                    {
                                      answer = answer.join(lcRelTemp);
                                      answer = answer.projection(temp);

                                    }

                                    notOperatorlc--;
                                    Relation toBeMinuslc = new Relation(null,null,null);

                                }
                                else
                                answer = lcRel;

                              }


                      }

                        return answer;
                    }


                  }
                  else
                  {

                    Vector boundVarExists = tree.getVarlist();
                    Vector freeVariableChild = lcRel.getAttributes();
                    Vector temp = new Vector();
                    for(int i=0; i<freeVariableChild.size();i++)
                    {
                      if(boundVarExists.contains(freeVariableChild.elementAt(i))){}
                      else
                      temp.addElement(freeVariableChild.elementAt(i));
                    }
                      lcRel = lcRel.projection(temp);
                    return lcRel;
                  }

                 }
                 else
                 {
                   Relation lcRel = evaluateDRC(lc);

                   Vector boundVarExists = tree.getVarlist();
                   Vector freeVariableChild = lcRel.getAttributes();
                   Vector temp = new Vector();
                   for(int i=0; i<freeVariableChild.size();i++)
                   {
                     if(boundVarExists.contains(freeVariableChild.elementAt(i))){}
                     else
                     temp.addElement(freeVariableChild.elementAt(i));
                  }
                  lcRel = lcRel.projection(temp);
                   return lcRel;
                 }

               }
            }
      else // and , or
          {
            if (tree.getRnodetype().equals("and"))
               {


                DRCNode rc = tree.getRchild();
                DRCNode lc = tree.getLchild();

                if( lc.getRnodetype().equals("comp") )
                  {
                    if( rc.getRnodetype().equals("comp"))
                    {

                        Vector combineVar = new Vector();
                        Relation rcRel = evaluateDRC(rc);
                        Relation lcRel = evaluateDRC(lc);
                        combineVar = rc.getSelectionVarList();
                        Vector temp = lc.getSelectionVarList();
                        for (int i=0; i<temp.size(); i++)
                        {
                          combineVar.addElement(temp.elementAt(i));
                        }

                        tree.setSelectionVarList(combineVar);
                    }
                    else if( rc.getRnodetype().equals("predicate"))
                    {
                      Relation rcRel = evaluateDRC(rc);
                      Relation lcRel = evaluateDRC(lc);


                      Relation answer = rcRel;
                      Vector combineVar = new Vector();
                      combineVar = lc.getSelectionVarList();


                      tree.setSelectionVarList(combineVar);

                      Vector arguments = answer.getAttributes();

                       for (int j=0; j<arguments.size(); j++)
                       {
                         String argname = (String) arguments.elementAt(j);

                        for (int i=0; i<combineVar.size(); i=i+5)
                         {

                          String lDataType = (String) combineVar.elementAt(i);
                          String lName = (String) combineVar.elementAt(i+1);
                          String cmpOp = (String) combineVar.elementAt(i+2);
                          String rDataType = (String) combineVar.elementAt(i+3);
                          String rName = (String) combineVar.elementAt(i+4);


                          if (argname.equals(lName) && rDataType.equals("str"))
                          {
                            answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                          }
                          else if (argname.equals(lName) && rDataType.equals("num"))
                          {
                            answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                          }
                          else if(argname.equals(lName) && rDataType.equals("col"))
                          {
                            if(arguments.contains(rName))
                            answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                            else{}

                          }
                         }
                       }


                    }
                    else if( rc.getRnodetype().equals("not"))
                    {

                      Relation rcRel = evaluateDRC(rc);
                      toBeMinus = rcRel;
                      Relation lcRel = evaluateDRC(lc);
                      return lcRel;

                    }
                    else
                    {
                        Relation rcRel = evaluateDRC(rc);
                        Relation lcRel = evaluateDRC(lc);
                        Vector combineVar = new Vector();


                        Relation answer = null;

                        if(rcRel == null)
                        {
                          combineVar = rc.getSelectionVarList();
                          Vector temp = lc.getSelectionVarList();
                          for (int i=0; i<temp.size(); i++)
                          {
                            combineVar.addElement(temp.elementAt(i));
                          }

                          tree.setSelectionVarList(combineVar);
                        }
                        else
                        {
                           answer = rcRel;

                           combineVar = rc.getSelectionVarList();
                           Vector temp = lc.getSelectionVarList();
                           for (int i=0; i<temp.size(); i++)
                           {
                            combineVar.addElement(temp.elementAt(i));
                           }


                           tree.setSelectionVarList(combineVar);
                          Vector arguments = answer.getAttributes();
                           for (int j=0; j<arguments.size(); j++)
                            {
                               String argname = (String) arguments.elementAt(j);

                              for (int i=0; i<combineVar.size(); i=i+5)
                               {

                                String lDataType = (String) combineVar.elementAt(i);
                                String lName = (String) combineVar.elementAt(i+1);
                                String cmpOp = (String) combineVar.elementAt(i+2);
                                String rDataType = (String) combineVar.elementAt(i+3);
                                String rName = (String) combineVar.elementAt(i+4);

                                if (argname.equals(lName) && rDataType.equals("str"))
                                {
                                  answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                }
                                else if (argname.equals(lName) && rDataType.equals("num"))
                                {
                                  answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                }
                                else if(argname.equals(lName) && rDataType.equals("col"))
                                {
                                  if(arguments.contains(rName))
                                  answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                  else{}

                                }
                               }
                             }

                            return answer;
                        }
                    }

                  }

                else if( lc.getRnodetype().equals("not"))
                    {
                      Relation lcRel = evaluateDRC(lc);
                      toBeMinuslc = lcRel;
                      if(rc.getRnodetype().equals("not"))
                      {
                        Relation rcRel = evaluateDRC(rc);
                        toBeMinus = rcRel;
                          notOperatorlc++;
                        return null;

                      }
                      else
                      {
                      Relation rcRel = evaluateDRC(rc);
                      notOperatorlc++;
                      return rcRel;
                      }


                    }

                // if lchild of 'and' node is not comp or not type
                else
                  {

                    if(rc.getRnodetype().equals("predicate"))
                      {

                        Relation rcRel = evaluateDRC(rc);
                        Relation lcRel = evaluateDRC(lc);
                        Relation answer = lcRel.join(rcRel);
                        Vector arguments = answer.getAttributes();

                        return answer;
                      }

                    else if( rc.getRnodetype().equals("comp"))
                      {

                        Relation rcRel = evaluateDRC(rc);
                        Relation lcRel = evaluateDRC(lc);


                        Relation answer = lcRel;
                        Vector combineVar = new Vector();
                        combineVar = rc.getSelectionVarList();


                        tree.setSelectionVarList(combineVar);

                        Vector arguments = answer.getAttributes();

                         for (int j=0; j<arguments.size(); j++)
                         {
                           String argname = (String) arguments.elementAt(j);

                          for (int i=0; i<combineVar.size(); i=i+5)
                           {

                            String lDataType = (String) combineVar.elementAt(i);
                            String lName = (String) combineVar.elementAt(i+1);
                            String cmpOp = (String) combineVar.elementAt(i+2);
                            String rDataType = (String) combineVar.elementAt(i+3);
                            String rName = (String) combineVar.elementAt(i+4);


                            if (argname.equals(lName) && rDataType.equals("str"))
                            {
                              answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                            }
                            else if (argname.equals(lName) && rDataType.equals("num"))
                            {
                              answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                            }
                            else if(argname.equals(lName) && rDataType.equals("col"))
                            {
                              if(arguments.contains(rName))
                              answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                              else{}

                            }
                           }
                         }

                         return answer;
                        }
                    else if( rc.getRnodetype().equals("not"))
                      {

                        Relation rcRel = evaluateDRC(rc);
                        toBeMinus =rcRel;

                        Relation lcRel = evaluateDRC(lc);
                        return lcRel;
                      }
                     else
                      {



                          Relation rcRel = evaluateDRC(rc);
                          Relation lcRel = evaluateDRC(lc);


                          Relation answer = null;

                          if(rcRel != null)
                          {
                            answer = lcRel.join(rcRel);
                          }
                          else
                          {

                            answer = lcRel;

                          }
                           Vector combineVar = new Vector();
                           combineVar = rc.getSelectionVarList();


                           tree.setSelectionVarList(combineVar);
                            Vector arguments = answer.getAttributes();

                           for (int j=0; j<arguments.size(); j++)
                            {
                              String argname = (String) arguments.elementAt(j);
                              for (int i=0; i<combineVar.size(); i=i+5)
                               {

                                String lDataType = (String) combineVar.elementAt(i);
                                String lName = (String) combineVar.elementAt(i+1);
                                String cmpOp = (String) combineVar.elementAt(i+2);
                                String rDataType = (String) combineVar.elementAt(i+3);
                                String rName = (String) combineVar.elementAt(i+4);


                                if (argname.equals(lName) && rDataType.equals("str"))
                                {
                                  answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                }
                                else if (argname.equals(lName) && rDataType.equals("num"))
                                {
                                  answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                }
                                else if(argname.equals(lName) && rDataType.equals("col"))
                                {
                                  if(arguments.contains(rName))
                                  answer = answer.selection(lDataType,lName,cmpOp,rDataType,rName);
                                  else{}

                                }


                               }
                             }

                             return answer;
                        }
                      }

                    }// end of "and" node

            else //or
              {
                DRCNode rc = tree.getRchild();
                DRCNode lc = tree.getLchild();
                Relation rcRel = evaluateDRC(rc);
                Relation lcRel = evaluateDRC(lc);

                Relation answer = lcRel.union(rcRel);
                return answer;
              }


          } // end of and, or
        } //end of not null tree

         return null;

  } // end of method


static String readInput() {
  try {
    StringBuffer buffer = new StringBuffer();
    System.out.flush();
    int c = System.in.read();
    while(c != '}' && c != -1) {
      if (c != '\n')
        buffer.append((char)c);
      else {
        buffer.append(" ");
        System.out.print("DRC> ");
        System.out.flush();
      }
      c = System.in.read();
      if (c == ';') {
        System.out.flush();
        break;
      }
    }
    return buffer.toString().trim();
  } catch (IOException e) {
      return "";
    }
}

}
